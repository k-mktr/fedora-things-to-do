# Fedora Workstation NATTD Not Another "Things To Do"!
# Initial System Setup Shell Script Builder for Fedora Workstation
#
# This application is a Streamlit-based web interface that allows users to customize
# and generate a shell script for setting up a fresh Fedora Workstation installation.
# It provides options for system configuration, essential and additional app installation,
# and system customization. The app uses predefined profiles and allows users to select
# individual options or apply preset profiles. It generates a downloadable shell script
# based on the user's selections, which can be run on a Fedora system to automate the
# setup process.
#
# This tool aims to simplify the post-installation process for Fedora users,
# allowing for easy customization and automation of common setup tasks.
#
# Author: Karl Stefan Danisz
# Contact: https://mktr.sbs/linkedin
# GitHub: https://mktr.sbs/github
# Version: 25.03
#
#
# Use responsibly, and always check the script you are about to run.
# This script is licensed under the GNU General Public License v3.0
#
import logging
import streamlit as st
from ui import render_sidebar, render_main_panel
from utils import AppState

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to INFO
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
