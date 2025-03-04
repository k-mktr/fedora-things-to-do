from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import streamlit as st

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
    
    def update_options(self, options: Dict[str, Any]) -> None:
        """
        Update the options in the application state.
        
        Args:
            options (Dict[str, Any]): A dictionary of options to update.
        """
        self.system_config = options.get("system_config", {})
        self.essential_apps = options.get("essential_apps", {})
        self.additional_apps = options.get("additional_apps", {})
        self.customization = options.get("customization", {})
        
        if "hostname" in options:
            self.hostname = options["hostname"]
        
        if "custom_script" in options:
            self.custom_script = options["custom_script"]
    
    def get_options(self) -> Dict[str, Any]:
        """
        Get the current options from the application state.
        
        Returns:
            Dict[str, Any]: A dictionary containing the current options.
        """
        options = {
            "system_config": self.system_config,
            "essential_apps": self.essential_apps,
            "additional_apps": self.additional_apps,
            "customization": self.customization
        }
        
        if self.hostname:
            options["hostname"] = self.hostname
            
        if hasattr(self, 'custom_script'):
            options["custom_script"] = self.custom_script
            
        return options
    
    def set_script_built(self, built: bool) -> None:
        """
        Set the script built status.
        
        Args:
            built (bool): Whether the script has been built.
        """
        self.script_built = built
    
    def set_full_script(self, script: str) -> None:
        """
        Set the full generated script.
        
        Args:
            script (str): The full generated script.
        """
        self.full_script = script 