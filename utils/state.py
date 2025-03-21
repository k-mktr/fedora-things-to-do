from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import streamlit as st
import copy
import logging

# Import at module level to avoid circular imports
try:
    from scripts.builder import process_all_dependencies
    from utils import load_nattd
except ImportError:
    # These will be imported dynamically if import fails at module level
    process_all_dependencies = None
    load_nattd = None

@dataclass
class AppState:
    """
    A class to manage the application state.
    """
    system_config: Dict[str, Any] = field(default_factory=dict)
    essential_apps: Dict[str, Any] = field(default_factory=dict)
    additional_apps: Dict[str, Any] = field(default_factory=dict)
    customization: Dict[str, Any] = field(default_factory=dict)
    hostname: Optional[str] = None
    output_mode: str = "Verbose"
    script_built: bool = False
    full_script: Optional[str] = None
    dependency_notifications: List[str] = field(default_factory=list)
    
    @staticmethod
    def get_instance():
        """
        Get or create an instance of AppState from Streamlit session state.
        
        Returns:
            AppState: An instance of the AppState class.
        """
        if 'app_state' not in st.session_state:
            st.session_state.app_state = AppState()
        return st.session_state.app_state
    
    def get_options(self) -> Dict[str, Any]:
        """
        Get the current options as a dictionary.
        
        Returns:
            Dict[str, Any]: The current options.
        """
        # Use deep copy for nested dictionaries
        options = {
            "system_config": copy.deepcopy(self.system_config),
            "essential_apps": copy.deepcopy(self.essential_apps),
            "additional_apps": copy.deepcopy(self.additional_apps),
            "customization": copy.deepcopy(self.customization),
        }
        
        if self.hostname is not None:
            options["hostname"] = self.hostname
            
        if hasattr(self, 'custom_script'):
            options["custom_script"] = self.custom_script
            
        return options
    
    def _update_state(self, options: Dict[str, Any]) -> None:
        """
        Internal method to update the state with new options.
        
        Args:
            options (Dict[str, Any]): The options to update the state with.
        """
        self.system_config = copy.deepcopy(options.get("system_config", {}))
        self.essential_apps = copy.deepcopy(options.get("essential_apps", {}))
        self.additional_apps = copy.deepcopy(options.get("additional_apps", {}))
        self.customization = copy.deepcopy(options.get("customization", {}))
        
        if "hostname" in options:
            self.hostname = options["hostname"]
        
        if "custom_script" in options:
            self.custom_script = options["custom_script"]
    
    def update_options(self, options: Dict[str, Any]) -> None:
        """
        Update the options in the application state and process dependencies.
        
        Args:
            options (Dict[str, Any]): A dictionary of options to update.
        """
        try:
            # Import dependencies if not already imported
            global process_all_dependencies, load_nattd
            if process_all_dependencies is None or load_nattd is None:
                from scripts.builder import process_all_dependencies
                from utils import load_nattd
            
            # Process dependencies first
            nattd_data = load_nattd()
            updated_options, notifications = process_all_dependencies(options, nattd_data)
            
            # Update state with processed options
            self._update_state(updated_options)
            
            # Update dependency notifications
            self.dependency_notifications = notifications
            
        except Exception as e:
            # If dependency processing fails, update with original options
            logging.error(f"Error processing dependencies: {str(e)}", exc_info=True)
            self._update_state(options)
            self.dependency_notifications = []
    
    def set_full_script(self, script: str) -> None:
        """
        Set the full generated script.
        
        Args:
            script (str): The generated script.
        """
        self.full_script = script
        self.script_built = True
    
    def set_script_built(self, built: bool) -> None:
        """
        Set whether a script has been built.
        
        Args:
            built (bool): Whether the script has been built.
        """
        self.script_built = built 