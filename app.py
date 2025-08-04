"""Fedora Workstation NATTD (Not Another 'Things To Do'!)

A Streamlit-based web application for generating customized setup scripts for Fedora Workstation.
This tool simplifies the post-installation process by providing an intuitive interface for:
- System configuration
- Essential and additional app installation
- System customization
- Script generation and download

The application allows users to:
1. Select system configurations
2. Choose essential and additional applications
3. Customize system settings
4. Generate and download a shell script
5. Apply predefined profiles

Features:
- Interactive web interface
- Modular script generation
- Dependency management
- Profile-based configurations
- Customizable installation options

Author: Karl Stefan Danisz
Contact: https://mktr.sbs/linkedin
GitHub: https://mktr.sbs/github
Version: 25.08 / 100 Stars Edition
License: GNU General Public License v3.0

Usage:
    streamlit run app.py

Note:
    Always review generated scripts before execution. This tool provides automation
    but requires user verification for system safety.
"""

import logging
import streamlit as st
from ui import render_sidebar, render_main_panel
from utils import AppState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configure Streamlit page
st.set_page_config(
    page_title="Fedora Things To Do",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/k-mktr/fedora-things-to-do/issues',
        'Report a bug': "https://github.com/k-mktr/fedora-things-to-do/issues",
        'About': """
        #### Not Another "Things To Do"!    
        **Fedora Workstation Setup Script Builder**
        
        A Shell Script Builder for setting up Fedora Workstation after a fresh install.
        
        If you find this tool useful, consider sharing it with others.

        Created by [Karl Stefan Danisz](https://mktr.sbs/linkedin)        
        
        [GitHub Repository](https://github.com/k-mktr/fedora-things-to-do)
        """
    }
)

def initialize_state():
    """
    Initialize the application state.
    """
    if 'app_state' not in st.session_state:
        # Create AppState instance
        app_state = AppState.get_instance()
        logging.info("Application state initialized")

def main():
    """
    Main application function that orchestrates the UI rendering and application flow.
    """
    logging.info("Starting main function")
    
    # Initialize application state
    initialize_state()
    
    # Render the sidebar with configuration options
    render_sidebar()
    
    # Render the main panel with script preview and download options
    render_main_panel()
    
    logging.info("Main function completed")

if __name__ == "__main__":
    main()
