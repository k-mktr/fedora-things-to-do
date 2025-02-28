import os
import logging
from typing import Dict, Any

def load_bonus_scripts() -> Dict[str, Dict[str, Any]]:
    """
    Load bonus scripts from the bonus directory.
    
    Returns:
        Dict[str, Dict[str, Any]]: A dictionary of bonus scripts with their names,
                                  content, and descriptions.
    """
    bonus_scripts = {}
    bonus_dir = "bonus"
    
    try:
        # Check if bonus directory exists
        if not os.path.exists(bonus_dir):
            logging.warning(f"Bonus directory '{bonus_dir}' does not exist.")
            return bonus_scripts
            
        # List files in the bonus directory
        for filename in os.listdir(bonus_dir):
            if filename.endswith(".sh"):
                try:
                    with open(os.path.join(bonus_dir, filename), 'r') as file:
                        script_content = file.read()
                        script_name = os.path.splitext(filename)[0].replace("_", " ").title()
                        
                        # Default description
                        description = "This script provides additional customization options."
                        
                        # Special descriptions for known scripts
                        if filename == "template_files.sh":
                            description = "Creates common file templates in your home directory for quick access."
                        elif filename == "install_nvidia.sh":
                            description = "Installs NVIDIA drivers. Run this script only after performing a full system upgrade and reboot of your system."
                        elif filename == "system_cleanup.sh":
                            description = "Cleans up your system from unnecessary files."
                        
                        # Store script information
                        bonus_scripts[script_name] = {
                            "filename": filename,
                            "content": script_content,
                            "description": description
                        }
                        
                        logging.debug(f"Loaded bonus script: {script_name}")
                except Exception as e:
                    logging.error(f"Error loading bonus script '{filename}': {str(e)}")
    except Exception as e:
        logging.error(f"Error accessing bonus scripts directory: {str(e)}")
    
    return bonus_scripts 