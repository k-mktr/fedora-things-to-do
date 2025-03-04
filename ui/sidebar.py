import streamlit as st
import re
import logging
from typing import Dict, Any, Tuple

from utils import load_nattd, generate_options, load_bonus_scripts, AppState

def matches_search(item_name: str, description: str, search_query: str) -> bool:
    """
    Check if an item matches the search query.
    
    Args:
        item_name (str): The name of the item to check.
        description (str): The description of the item to check.
        search_query (str): The search query to match against.
        
    Returns:
        bool: True if the item matches the search query, False otherwise.
    """
    if not search_query:
        return True
    pattern = re.compile(search_query, re.IGNORECASE)
    return pattern.search(item_name) is not None or pattern.search(description) is not None

def render_sidebar() -> None:
    """
    Render the sidebar with configuration options.
    Updates the application state with user selections.
    """
    app_state = AppState.get_instance()
    nattd_data = load_nattd()
    all_options = generate_options()
    
    # Add centered, clickable logo to the top of the sidebar using HTML
    st.sidebar.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; padding: 10px;">
            <a href="/" target="_self">
                <img src="https://github.com/k-mktr/fedora-things-to-do/blob/master/assets/logo.png?raw=true" width="250" alt="Logo">
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.sidebar.header("Configuration Options")
    
    # Initialize options in the app state if not already present
    options = app_state.get_options()
    
    # Output mode selection
    output_mode = st.sidebar.radio(
        "Output Mode", 
        ["Quiet", "Verbose"], 
        index=1, 
        help="""
        Choose how the script will display its progress:
        
        **Verbose** (Recommended):
        - Shows all command outputs
        - Displays detailed progress information
        - Helps you understand what's happening
        - Better for troubleshooting
        
        **Quiet**:
        - Hides most command outputs
        - Shows only essential messages
        - Cleaner terminal output
        - Faster execution
        """
    )
    app_state.output_mode = output_mode
    
    # Add search bar at the top of the sidebar
    search_query = st.sidebar.text_input(
        "🔍 Search options and apps", 
        "",
        help="Search through all available options and applications. The sidebar will automatically expand matching sections."
    )
    
    # System Configuration section
    try:
        # Check if system_config exists and has the expected structure
        if "system_config" not in nattd_data or not isinstance(nattd_data["system_config"], dict):
            st.sidebar.error("Error: system_config data is missing or invalid")
            logging.error(f"Invalid system_config data: {nattd_data.get('system_config')}")
            system_config_matches = False
        else:
            system_config_matches = any(
                option in nattd_data["system_config"] and 
                isinstance(nattd_data["system_config"][option], dict) and
                "name" in nattd_data["system_config"][option] and
                "description" in nattd_data["system_config"][option] and
                matches_search(
                    nattd_data["system_config"][option]["name"], 
                    nattd_data["system_config"][option]["description"],
                    search_query
                ) for option in all_options["system_config"]
            )
    except Exception as e:
        st.sidebar.error(f"Error checking system configuration options: {str(e)}")
        logging.error(f"Error in system configuration section: {str(e)}", exc_info=True)
        system_config_matches = False
    
    # Initialize rpm_fusion_checkbox variable
    rpm_fusion_checkbox = False
    
    with st.sidebar.expander("System Configuration", expanded=system_config_matches and bool(search_query)):
        for option in all_options["system_config"]:
            try:
                # Ensure option exists and has required keys
                if (option in nattd_data["system_config"] and 
                    isinstance(nattd_data["system_config"][option], dict) and
                    "name" in nattd_data["system_config"][option] and
                    "description" in nattd_data["system_config"][option] and
                    matches_search(
                        nattd_data["system_config"][option]["name"], 
                        nattd_data["system_config"][option]["description"],
                        search_query
                    )):
                    
                    logging.debug(f"Processing option: {option}")
                    
                    # Special handling for RPM Fusion
                    if option == "enable_rpmfusion":
                        rpm_fusion_checkbox = st.checkbox(
                            nattd_data["system_config"][option]["name"],
                            key=f"system_config_{option}",
                            help=nattd_data["system_config"][option]["description"]
                        )
                        options["system_config"][option] = rpm_fusion_checkbox
                    else:
                        options["system_config"][option] = st.checkbox(
                            nattd_data["system_config"][option]["name"],
                            key=f"system_config_{option}",
                            help=nattd_data["system_config"][option]["description"]
                        )
                    
                    if option == "set_hostname" and options["system_config"][option]:
                        hostname = st.text_input("Enter the new hostname:", value=app_state.hostname or "")
                        options["hostname"] = hostname
                        app_state.hostname = hostname
            except Exception as e:
                st.sidebar.error(f"Error rendering option '{option}': {str(e)}")
                logging.error(f"Error rendering option '{option}': {str(e)}", exc_info=True)
            
            if search_query and option not in nattd_data["system_config"]:
                st.empty()  # Placeholder to keep expander visible

        # Check if any codec option is selected and update RPM Fusion checkbox
        try:
            codec_options = ["install_multimedia_codecs", "install_intel_codecs", "install_amd_codecs"]
            if any(option in options["system_config"] and options["system_config"].get(option, False) 
                  for option in codec_options):
                options["system_config"]["enable_rpmfusion"] = True
                if not rpm_fusion_checkbox:
                    st.sidebar.info("""
                    **RPM Fusion** has been automatically selected because you chose to install codecs.
                    This is required for proper multimedia support on Fedora.
                    """)
        except Exception as e:
            logging.error(f"Error in codec options check: {str(e)}", exc_info=True)

    # Essential Apps section
    try:
        essential_apps_matches = "essential_apps" in nattd_data and "apps" in nattd_data["essential_apps"] and any(
            isinstance(app, dict) and "name" in app and "description" in app and
            matches_search(app["name"], app["description"], search_query) 
            for app in nattd_data["essential_apps"]["apps"]
        )
    except Exception as e:
        st.sidebar.error(f"Error checking essential apps: {str(e)}")
        logging.error(f"Error in essential apps check: {str(e)}", exc_info=True)
        essential_apps_matches = False
    
    with st.sidebar.expander("Essential Applications", expanded=essential_apps_matches and bool(search_query)):
        try:
            if "essential_apps" in nattd_data and "apps" in nattd_data["essential_apps"]:
                essential_apps = nattd_data["essential_apps"]["apps"]
                for app in essential_apps:
                    if isinstance(app, dict) and "name" in app and "description" in app and matches_search(app["name"], app["description"], search_query):
                        options["essential_apps"][app["name"]] = st.checkbox(
                            app["name"],
                            key=f"essential_app_{app['name']}",
                            help=app["description"]
                        )
            else:
                st.sidebar.warning("No essential applications found")
        except Exception as e:
            st.sidebar.error(f"Error rendering essential apps: {str(e)}")
            logging.error(f"Error rendering essential apps: {str(e)}", exc_info=True)
        
        if search_query:
            st.empty()  # Placeholder to keep expander visible

    # Additional Applications section
    try:
        additional_apps_matches = "additional_apps" in nattd_data and any(
            isinstance(category_data, dict) and "apps" in category_data and
            isinstance(category_data["apps"], dict) and any(
                isinstance(app_info, dict) and "name" in app_info and "description" in app_info and
                matches_search(app_info['name'], app_info['description'], search_query)
                for app_info in category_data["apps"].values()
            )
            for category_data in nattd_data["additional_apps"].values() 
        )
    except Exception as e:
        st.sidebar.error(f"Error checking additional apps: {str(e)}")
        logging.error(f"Error in additional apps check: {str(e)}", exc_info=True)
        additional_apps_matches = False
    
    with st.sidebar.expander("Additional Applications", expanded=additional_apps_matches and bool(search_query)):
        try:
            if "additional_apps" in nattd_data:
                for category, category_data in nattd_data["additional_apps"].items():
                    if isinstance(category_data, dict) and "name" in category_data and "apps" in category_data:
                        st.subheader(category_data["name"])
                        options["additional_apps"][category] = {}
                        category_has_matches = False
                        
                        for app_id, app_info in category_data["apps"].items():
                            if isinstance(app_info, dict) and "name" in app_info and "description" in app_info and matches_search(app_info['name'], app_info['description'], search_query):
                                app_selected = st.checkbox(
                                    app_info['name'], 
                                    key=f"app_{category}_{app_id}", 
                                    help=app_info['description']
                                )
                                options["additional_apps"][category][app_id] = {'selected': app_selected}
                                
                                if app_selected and 'installation_types' in app_info:
                                    installation_type = st.radio(
                                        f"Choose {app_info['name']} installation type:",
                                        list(app_info['installation_types'].keys()),
                                        key=f"{category}_{app_id}_install_type"
                                    )
                                    options["additional_apps"][category][app_id]['installation_type'] = installation_type
                                
                                category_has_matches = True
                        
                        if not category_has_matches and search_query:
                            st.empty()  # Placeholder to keep category visible
            else:
                st.sidebar.warning("No additional applications found")
        except Exception as e:
            st.sidebar.error(f"Error rendering additional apps: {str(e)}")
            logging.error(f"Error rendering additional apps: {str(e)}", exc_info=True)

    # Customization section
    try:
        customization_matches = "customization" in nattd_data and "apps" in nattd_data["customization"] and any(
            isinstance(app_info, dict) and "name" in app_info and "description" in app_info and
            matches_search(app_info['name'], app_info['description'], search_query) 
            for app_info in nattd_data["customization"]["apps"].values()
        )
    except Exception as e:
        st.sidebar.error(f"Error checking customization options: {str(e)}")
        logging.error(f"Error in customization check: {str(e)}", exc_info=True)
        customization_matches = False
    
    with st.sidebar.expander("Customization", expanded=customization_matches and bool(search_query)):
        try:
            if "customization" in nattd_data and "apps" in nattd_data["customization"]:
                customization_apps = nattd_data["customization"]["apps"]
                for app_id, app_info in customization_apps.items():
                    if isinstance(app_info, dict) and "name" in app_info and "description" in app_info and matches_search(app_info['name'], app_info['description'], search_query):
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
            else:
                st.sidebar.warning("No customization options found")
        except Exception as e:
            st.sidebar.error(f"Error rendering customization options: {str(e)}")
            logging.error(f"Error rendering customization options: {str(e)}", exc_info=True)
        
        if search_query:
            st.empty()  # Placeholder to keep expander visible

    # Advanced section for custom script
    with st.sidebar.expander("Advanced"):
        st.warning("""
        ⚠️ **Caution**: This section is for advanced users. Incorrect shell commands can potentially harm your system. Use with care.
        """)
        
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

    # Bonus Scripts section
    with st.sidebar.expander("Bonus Scripts"):
        st.warning("""
        ⚠️ **Caution**: These are standalone scripts for additional customization. 
        Download and run them separately after your initial setup and system reboot.
        """)

        try:
            bonus_scripts = load_bonus_scripts()
            if bonus_scripts:
                for script_name, script_data in bonus_scripts.items():
                    st.markdown(f"**{script_name}**")
                    st.markdown(script_data["description"])
                    st.download_button(
                        label=f"Download {script_name} Script",
                        data=script_data["content"],
                        file_name=script_data["filename"],
                        mime="text/plain",
                        key=f"download_{script_name.lower().replace(' ', '_')}"
                    )
                    st.markdown("---")
            else:
                st.info("No bonus scripts found. They will be available in the 'bonus' directory once you create it.")
        except Exception as e:
            st.sidebar.error(f"Error loading bonus scripts: {str(e)}")
            logging.error(f"Error loading bonus scripts: {str(e)}", exc_info=True)

    # Placeholder at the bottom of the sidebar
    sidebar_bottom = st.sidebar.empty()
    sidebar_bottom.markdown("""
    <style>
        .link-bar {
            display: flex;
            justify-content: center;
            animation: fadeIn 1s ease-out 0.9s;
            opacity: 0;
            animation-fill-mode: forwards;
            text-align: center;
        }
        .link-bar a {
            text-decoration: none;
            font-weight: bold;
            color: #8da9c4;
        }
        .link-bar a:hover {
            text-decoration: underline;
        }
        .separator {
            width: 100%;
            border-top: 1px solid #8da9c4;
            margin: 21px 0;
        }
        @media (max-width: 600px) {
            .link-bar {
                flex-direction: column;
                gap: 10px;
            }
        }
    </style>
    <div class="link-bar">
        <a href="https://fedoraproject.org/workstation/" target="_blank" style="text-decoration: none;" aria-label="Fedora Workstation">Still on the fence?<br>Grab your Fedora now!</a>
    </div>
    <div class="separator"></div>
    <div style="text-align: center; padding: 21px 0;">
        <p style="margin-bottom: 5px;">Created with ❤️ for Open Source</p>
        <a href="https://mktr.sbs/linkedin" target="_blank" style="text-decoration: none; color: #8da9c4;" aria-label="Karol Stefan Danisz LinkedIn">
            <i>by Karol Stefan Danisz</i>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Update the app state with the current options
    app_state.update_options(options) 