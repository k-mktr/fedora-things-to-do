# Fedora Workstation NYATTD Not Yet Another "Things To Do"!
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
# Author: Karol Stefan Danisz
# Contact: https://mktr.sbs/linkedin
# Version: 24.08
#
#
# Use responsibly, and always check the script you are about to run.
# This script is licensed under the GNU General Public License v3.0
#
import logging
import streamlit as st
from typing import Dict, Any
import builder

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO in production
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Constants
SCRIPT_TEMPLATE_PATH = 'template.sh'

st.set_page_config(
    page_title="Fedora Things To Do",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/k-mktr/fedora-things-to-do/issues',
        'Report a bug': "https://github.com/k-mktr/fedora-things-to-do/issues",
        'About': """
        #### Not Yet Another "Things To Do"!    
        **Fedora Workstation Setup Script Builder**
        
        A Shell Script Builder for setting up Fedora Workstation after a fresh install.
        
        If you find this tool useful, consider sharing it with others.

        Created by [Karol Stefan Danisz](https://mktr.sbs/linkedin)        
        
        [GitHub Repository](https://github.com/k-mktr/fedora-things-to-do)
        """
    }
)

def load_template() -> str:
    with open(SCRIPT_TEMPLATE_PATH, 'r') as file:
        return file.read()

def render_sidebar() -> Dict[str, Any]:
    st.sidebar.header("Configuration Options")
    options = {"system_config": {}, "essential_apps": {}, "additional_apps": {}, "customization": {}}

    output_mode = st.sidebar.radio("Output Mode", ["Quiet", "Verbose"], index=0, help="Select the output mode for the script.")

    all_options = builder.generate_options()
    nyattd_data = builder.load_nyattd()

    logging.debug(f"all_options: {all_options}")
    logging.debug(f"nyattd_data['system_config']: {nyattd_data['system_config']}")

    # System Configuration section
    with st.sidebar.expander("System Configuration"):
        for option in all_options["system_config"]:
            logging.debug(f"Processing option: {option}")
            logging.debug(f"nyattd_data['system_config'][{option}]: {nyattd_data['system_config'][option]}")
            options["system_config"][option] = st.checkbox(
                nyattd_data["system_config"][option]["name"],
                key=f"system_config_{option}",
                help=nyattd_data["system_config"][option]["description"]
            )
            if option == "set_hostname" and options["system_config"][option]:
                options["hostname"] = st.text_input("Enter the new hostname:")

    # Essential Apps section
    with st.sidebar.expander("Essential Applications"):
        essential_apps = nyattd_data["essential_apps"]["apps"]
        for app in essential_apps:
            options["essential_apps"][app["name"]] = st.checkbox(
                app["name"],
                key=f"essential_app_{app['name']}",
                help=app["description"]
            )

    # Additional Applications section
    with st.sidebar.expander("Additional Applications"):
        for category, category_data in nyattd_data["additional_apps"].items():
            st.subheader(category_data["name"])
            options["additional_apps"][category] = {}
            for app_id, app_info in category_data["apps"].items():
                app_selected = st.checkbox(app_info['name'], key=f"app_{category}_{app_id}", help=app_info['description'])
                options["additional_apps"][category][app_id] = {'selected': app_selected}
                
                if app_selected and 'installation_types' in app_info:
                    installation_type = st.radio(
                        f"Choose {app_info['name']} installation type:",
                        list(app_info['installation_types'].keys()),
                        key=f"{category}_{app_id}_install_type"
                    )
                    options["additional_apps"][category][app_id]['installation_type'] = installation_type

    # Customization section
    with st.sidebar.expander("Customization"):
        customization_apps = nyattd_data["customization"]["apps"]
        for app_id, app_info in customization_apps.items():
            options["customization"][app_id] = st.checkbox(
                app_info['name'],
                key=f"customization_{app_id}",
                help=app_info['description']
            )
            
            # Special handling for Windows Fonts
            if app_id == "install_microsoft_fonts" and options["customization"][app_id]:
                options["customization"][app_id] = {
                    'selected': True,
                    'installation_type': st.radio(
                        "Windows Fonts Installation Method",
                        ('core', 'windows'),
                        format_func=lambda x: "Core Fonts" if x == "core" else "Windows Fonts",
                        key=f"customization_{app_id}_install_type",
                        help="Choose how to install Windows fonts."
                    )
                }
                
                if options["customization"][app_id]['installation_type'] == 'windows':
                    st.warning("⚠️ This method requires a valid Windows license. "
                               "Please ensure you comply with Microsoft's licensing terms.")
                    st.markdown("[Learn more about Windows fonts licensing](https://learn.microsoft.com/en-us/typography/fonts/font-faq)")

    # Advanced section for custom script
    with st.sidebar.expander("Advanced"):
        st.warning("⚠️ **Caution**: This section is for advanced users. Incorrect shell commands can potentially harm your system. Use with care.")
        
        st.markdown("""
        Guidelines for custom commands:
        - Ensure each command is on a new line
        - Test your commands before adding them here
        - Be aware that these commands will run with sudo privileges
        """)
        
        default_custom_script = 'echo "Created with ❤️ for Open Source"'
        options["custom_script"] = st.text_area(
            "Custom Shell Commands",
            value=default_custom_script,
            help="Enter any additional shell commands you want to run at the end of the script.",
            height=200,
            key="custom_script_input"
        )
        
        if options["custom_script"].strip() != default_custom_script:
            st.info("Remember to review your custom commands in the script preview before downloading.")

    
    # Create a placeholder at the bottom of the sidebar
    sidebar_bottom = st.sidebar.empty()
    sidebar_bottom.markdown("""
    ---
    <div style="text-align: center; padding: 21px 0;">
        <p style="margin-bottom: 5px;">Created with ❤️ for Open Source</p>
        <a href="https://mktr.sbs/linkedin" target="_blank" style="text-decoration: none; color: #8da9c4;">
            <i>by Karol Stefan Danisz</i>
        </a>
    </div>
    """, unsafe_allow_html=True)

    return options, output_mode


def build_script(options: Dict[str, Any], output_mode: str) -> str:
    script_parts = {
        "system_upgrade": builder.build_system_upgrade(options, output_mode),
        "system_config": builder.build_system_config(options, output_mode),
        "app_install": builder.build_app_install(options, output_mode),
        "customization": builder.build_customization(options, output_mode),
        "custom_script": builder.build_custom_script(options, output_mode),
    }
    
    preview_script = "(...)  # Script header and initial setup\n\n"
    
    for placeholder, content in script_parts.items():
        if content and content.strip():  # Check if content is not None and not empty
            preview_script += f"# {placeholder.replace('_', ' ').title()}\n"
            preview_script += content + "\n\n"
    
    preview_script += "(...)  # Script footer"
    
    # Replace the hostname placeholder if it exists
    if "hostname" in options:
        preview_script = preview_script.replace("{hostname}", options["hostname"])
    
    return preview_script

def build_full_script(template: str, options: Dict[str, Any], output_mode: str) -> str:
    script_parts = {
        "system_upgrade": builder.build_system_upgrade(options, output_mode),
        "system_config": builder.build_system_config(options, output_mode),
        "app_install": builder.build_app_install(options, output_mode),
        "customization": builder.build_customization(options, output_mode),
        "custom_script": builder.build_custom_script(options, output_mode),
    }
    
    for placeholder, content in script_parts.items():
        template = template.replace(f"{{{{{placeholder}}}}}", content)
    
    # Replace the hostname placeholder if it exists
    if "hostname" in options:
        template = template.replace("{hostname}", options["hostname"])
    
    return template

def main():
    logging.info("Starting main function")
    # Add a header with a logo and links
    st.markdown("""
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .header-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 2rem;
        }
        .logo {
            width: 400px;
            height: auto;
            margin-bottom: 1rem;
            animation: fadeIn 1s ease-out;
        }
        .main-header {
            font-size: 2.5em;
            font-weight: bold;
            text-align: center;
            margin-bottom: 0.5rem;
            animation: fadeIn 1s ease-out 0.3s;
            opacity: 0;
            animation-fill-mode: forwards;
        }
        .sub-header {
            font-size: 1.5em;
            text-align: center;
            font-style: italic;
            margin-bottom: 1rem;
            animation: fadeIn 1s ease-out 0.6s;
            opacity: 0;
            animation-fill-mode: forwards;
        }
        .link-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            animation: fadeIn 1s ease-out 0.9s;
            opacity: 0;
            animation-fill-mode: forwards;
        }
        .link-bar a {
            text-decoration: none;
            font-weight: bold;
        }
        .link-bar a:hover {
            text-decoration: underline;
        }
    </style>
    <div class="header-container">
        <img src="https://fedoraproject.org/assets/images/fedora-workstation-logo.png" alt="Fedora Logo" class="logo">
        <h1 class="main-header">Not Yet Another <i>'Things To Do'!</i></h1>
        <h2 class="sub-header">Fedora Workstation Initial System Setup Shell Script Builder</h2>
        <div class="link-bar">
            <a href="https://fedoraproject.org/workstation/" target="_blank" style="text-decoration: none; color: #8da9c4;" >Still on the fence? Grab your Fedora now!</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'script_built' not in st.session_state:
        st.session_state.script_built = False

    logging.info("Loading template")
    template = load_template()
    logging.info("Rendering sidebar")
    options, output_mode = render_sidebar()

    logging.info("Creating script preview")
    script_preview = st.empty()

    logging.info("Building script")
    updated_script = build_script(options, output_mode)
    logging.info("Displaying script preview")
    script_preview.code(updated_script, language="bash")

    if st.button("Build Your Script"):
        logging.info("Building full script")
        full_script = build_full_script(template, options, output_mode)
        st.session_state.full_script = full_script
        st.session_state.script_built = True

    # Display download button and instructions if script has been built
    if st.session_state.script_built:
        st.download_button(
            label="Download Your Script",
            data=st.session_state.full_script,
            file_name="fedora_setup_script.sh",
            mime="text/plain"
        )
        
        st.markdown("""
        ### Your Script Has Been Created!

        Follow these steps to use your script:

        1. **Download the Script**: Click the 'Download Your Script' button above to save the script to your computer.

        2. **Make the Script Executable**: Open a terminal, navigate to the directory containing the downloaded script, and run:
           ```
           chmod +x fedora_setup_script.sh
           ```

        3. **Run the Script**: Execute the script with sudo privileges:
           ```
           sudo ./fedora_setup_script.sh
           ```

        ⚠️ **Caution**: This script will make changes to your system. Please review the script contents before running and ensure you understand the modifications it will make.
        """)

    logging.info("Main function completed")

if __name__ == "__main__":
    main()
