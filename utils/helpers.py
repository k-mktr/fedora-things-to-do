import json
import logging
import streamlit as st
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_nattd() -> Dict[str, Any]:
    """
    Load and cache NATTD data from nattd.json file.
    
    Returns:
        Dict[str, Any]: The loaded NATTD data as a dictionary.
    """
    try:
        with open('nattd.json', 'r') as file:
            data = json.load(file)
            logging.debug("NATTD data loaded successfully")
            return data
    except Exception as e:
        logging.error(f"Error loading NATTD data: {str(e)}")
        # Return a minimal structure to prevent further errors
        return {
            "system_config": {},
            "essential_apps": {"apps": []},
            "additional_apps": {},
            "customization": {"apps": {}}
        }

def safely_load_file(file_path: str, default_content: str = "") -> str:
    """
    Safely load a file with error handling.
    
    Args:
        file_path (str): Path to the file to load.
        default_content (str, optional): Default content to return if loading fails.
            Defaults to empty string.
    
    Returns:
        str: The content of the file or default_content if loading fails.
    """
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error loading file '{file_path}': {str(e)}")
        return default_content

def should_quiet_redirect(command: str) -> bool:
    """
    Determine if a command should have quiet redirection.
    
    Args:
        command (str): The command to check.
    
    Returns:
        bool: True if the command should have quiet redirection, False otherwise.
    """
    # List of patterns that should not have quiet redirection
    noisy_patterns = ['dnf update', 'dnf upgrade', 'reboot']
    
    # Never redirect color_echo messages with supported colors
    command_clean = command.strip()
    if command_clean.startswith('color_echo') and any(
        command_clean.startswith(f'color_echo "{color}"') 
        for color in ['red', 'green', 'yellow', 'blue']
    ):
        return False
        
    return not any(pattern in command for pattern in noisy_patterns)

def generate_options() -> Dict[str, Any]:
    """
    Generate an options structure from the loaded NATTD data.
    
    Returns:
        Dict[str, Any]: A dictionary containing the options structure.
    """
    nattd_data = load_nattd()
    logging.debug(f"Generating options from NATTD data: {nattd_data}")
    
    options = {
        "system_config": list(nattd_data.get("system_config", {}).keys()),
        "essential_apps": [],
        "additional_apps": {},
        "customization": []
    }
    
    # Add essential apps
    for app in nattd_data.get("essential_apps", {}).get("apps", []):
        options["essential_apps"].append(app["name"])
    
    # Add additional apps categories
    for category, category_data in nattd_data.get("additional_apps", {}).items():
        options["additional_apps"][category] = list(category_data.get("apps", {}).keys())
    
    # Add customization options
    options["customization"] = list(nattd_data.get("customization", {}).get("apps", {}).keys())
    
    logging.debug(f"Generated options: {options}")
    return options 