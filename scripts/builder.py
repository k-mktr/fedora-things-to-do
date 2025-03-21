"""Script builder module for Fedora Workstation NATTD.

This module handles the generation of shell scripts based on user selections,
including dependency resolution and script composition.
"""

import logging
import copy
from typing import Dict, Any, List, Union, Optional, Tuple
from utils import load_nattd, should_quiet_redirect

# Constants for dependencies and configurations
DEPENDENCY_RPMFUSION = "enable_rpmfusion"
CODEC_OPTIONS = ["install_multimedia_codecs", "install_intel_codecs", "install_amd_codecs"]
DEFAULT_HOSTNAME = "fedora-workstation"

# Dependency descriptions for notifications
DEPENDENCY_MESSAGES = {
    DEPENDENCY_RPMFUSION: "RPM Fusion has been automatically enabled because it's required for {app_name}. This provides necessary packages and codecs."
}

def check_dependencies(options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check and handle system-level dependencies.
    
    Args:
        options: The selected options
        
    Returns:
        Updated options with dependencies resolved
    """
    # Make a deep copy of options to avoid modifying the original
    updated_options = copy.deepcopy(options)
    
    # Initialize system_config if it doesn't exist
    if "system_config" not in updated_options:
        updated_options["system_config"] = {}
    
    # Check if multimedia codecs or GPU codecs are selected
    if any(option in updated_options["system_config"] and updated_options["system_config"].get(option, False) 
           for option in CODEC_OPTIONS):
        # Ensure RPM Fusion is enabled
        updated_options["system_config"][DEPENDENCY_RPMFUSION] = True
        logging.info("RPM Fusion automatically enabled due to codec selection")
    
    return updated_options

def build_system_upgrade(options: Dict[str, Any], output_mode: str) -> str:
    """
    Build the system upgrade section of the script.
    
    Args:
        options: The selected options
        output_mode: The output mode (Quiet or Verbose)
        
    Returns:
        The system upgrade commands as a string
    """
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""
    
    upgrade_commands = [
        'color_echo "blue" "Performing system upgrade... This may take a while..."',
        f"dnf upgrade -y{quiet_redirect}",
        ""  # Add an empty line for readability
    ]
    
    return "\n".join(upgrade_commands)

def build_system_config(options: Dict[str, Any], output_mode: str) -> str:
    """
    Build the system configuration section of the script.
    
    Args:
        options: The selected options
        output_mode: The output mode (Quiet or Verbose)
        
    Returns:
        The system configuration commands as a string
    """
    config_commands = []
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""

    try:
        nattd_data = load_nattd()
        if "system_config" not in nattd_data:
            logging.error("System configuration data missing in NATTD")
            return "# Error: System configuration data not found\n"
            
        system_config = nattd_data["system_config"]

        # Check if system_config exists in options
        if "system_config" not in options:
            logging.warning("No system configuration options selected")
            return "# No system configuration options selected\n"
            
        for option, enabled in options["system_config"].items():
            if enabled and option in system_config:
                # Ensure the option has the expected structure
                if not isinstance(system_config[option], dict) or "command" not in system_config[option]:
                    logging.error(f"Invalid configuration for option '{option}'")
                    config_commands.append(f"# Error: Invalid configuration for {option}")
                    continue
                    
                description = system_config[option].get("description", f"Configure {option}")
                config_commands.append(f"# {description}")
                commands = system_config[option]["command"]
                
                if isinstance(commands, list):
                    for cmd in commands:
                        if option == "set_hostname" and "hostnamectl set-hostname" in cmd:
                            # Use a placeholder for the hostname
                            hostname = options.get("hostname", "fedora-workstation")
                            cmd = cmd.replace("{hostname}", hostname)
                        if output_mode == "Quiet" and should_quiet_redirect(cmd):
                            cmd += quiet_redirect
                        config_commands.append(cmd)
                else:
                    cmd = commands
                    if option == "set_hostname" and "hostnamectl set-hostname" in cmd:
                        # Use a placeholder for the hostname
                        hostname = options.get("hostname", "fedora-workstation")
                        cmd = cmd.replace("{hostname}", hostname)
                    if output_mode == "Quiet" and should_quiet_redirect(cmd):
                        cmd += quiet_redirect
                    config_commands.append(cmd)
                
                config_commands.append("")  # Add an empty line for readability
    except Exception as e:
        logging.error(f"Error building system configuration: {str(e)}", exc_info=True)
        return f"# Error building system configuration: {str(e)}\n"

    return "\n".join(config_commands)

def process_installation_dependencies(app_data: Dict[str, Any], install_type: str, options: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Process installation-type-specific dependencies for an app.
    
    Args:
        app_data: The application data from nattd.json
        install_type: The selected installation type (e.g., 'DNF', 'Flatpak')
        options: The selected options dictionary
        
    Returns:
        Tuple containing:
        - Updated options with dependencies resolved
        - List of notification messages about enabled dependencies
    """
    # Make a deep copy of options to avoid modifying the original
    updated_options = copy.deepcopy(options)
    notifications = []
    
    if ('installation_types' in app_data and 
        install_type in app_data['installation_types'] and 
        'dependencies' in app_data['installation_types'][install_type]):
        
        deps = app_data['installation_types'][install_type]['dependencies']
        if not isinstance(deps, list):
            deps = [deps]
            
        for dep in deps:
            if dep == DEPENDENCY_RPMFUSION:
                if "system_config" not in updated_options:
                    updated_options["system_config"] = {}
                # Only add notification if RPM Fusion wasn't already enabled
                if not updated_options["system_config"].get(DEPENDENCY_RPMFUSION, False):
                    updated_options["system_config"][DEPENDENCY_RPMFUSION] = True
                    app_name = app_data.get('name', 'this application')
                    notifications.append(DEPENDENCY_MESSAGES[DEPENDENCY_RPMFUSION].format(app_name=app_name))
                    logging.info(f"RPM Fusion automatically enabled due to {app_name} dependency")
    
    return updated_options, notifications

def build_app_install(options: Dict[str, Any], output_mode: str) -> str:
    """
    Build the application installation section of the script.
    
    Args:
        options: The selected options
        output_mode: The output mode (Quiet or Verbose)
        
    Returns:
        The application installation commands as a string
    """
    install_commands = []
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""

    try:
        nattd_data = load_nattd()
        
        # Essential apps
        if "essential_apps" in options and "essential_apps" in nattd_data and "apps" in nattd_data["essential_apps"]:
            essential_apps = [
                app for app in nattd_data["essential_apps"]["apps"] 
                if isinstance(app, dict) and "name" in app and 
                options["essential_apps"].get(app["name"], False)
            ]
            
            if essential_apps:
                install_commands.append("# Install essential applications")
                app_names = " ".join([app["name"] for app in essential_apps])
                install_commands.append('color_echo "yellow" "Installing essential applications..."')
                install_commands.append(f"dnf install -y {app_names}{quiet_redirect}")
                install_commands.append('color_echo "green" "Essential applications installed successfully."')
                install_commands.append("")

        # Additional apps
        if "additional_apps" in options and "additional_apps" in nattd_data:
            for category, category_data in options["additional_apps"].items():
                if category not in nattd_data["additional_apps"]:
                    continue
                    
                category_apps = [
                    app_id for app_id, app_data in category_data.items() 
                    if isinstance(app_data, dict) and app_data.get('selected', False)
                ]
                
                if category_apps:
                    install_commands.append(f"# Install {nattd_data['additional_apps'][category].get('name', category)} applications")
                    
                    for app_id in category_apps:
                        if app_id not in nattd_data['additional_apps'][category]['apps']:
                            install_commands.append(f"# Warning: App {app_id} not found in configuration")
                            continue
                            
                        app_data = nattd_data['additional_apps'][category]['apps'][app_id]
                        app_name = app_data.get('name', app_id)
                        install_commands.append(f'color_echo "yellow" "Installing {app_name}..."')
                        
                        # Handle different installation types
                        if ('installation_types' in app_data and 
                            isinstance(options["additional_apps"][category][app_id], dict) and
                            'installation_type' in options["additional_apps"][category][app_id]):
                            
                            install_type = options["additional_apps"][category][app_id]['installation_type']
                            if install_type in app_data['installation_types']:
                                commands = app_data['installation_types'][install_type].get('command', '')
                            else:
                                install_commands.append(f"# Warning: Installation type {install_type} not found for {app_name}")
                                continue
                        else:
                            commands = app_data.get("command", '')
                        
                        if not commands:
                            install_commands.append(f"# Warning: No command found for {app_name}")
                            continue
                            
                        if isinstance(commands, list):
                            for cmd in commands:
                                install_commands.append(f"{cmd}{quiet_redirect if should_quiet_redirect(cmd) else ''}")
                        else:
                            install_commands.append(f"{commands}{quiet_redirect if should_quiet_redirect(commands) else ''}")
                        
                        install_commands.append(f'color_echo "green" "{app_name} installed successfully."')
                        
                        # Add special note for Docker
                        if app_id == "install_docker":
                            install_commands.append("# Note: Docker group changes will take effect after logging out and back in")
                    
                    install_commands.append("")  # Add empty line for readability
    except Exception as e:
        logging.error(f"Error building application installation: {str(e)}", exc_info=True)
        return f"# Error building application installation: {str(e)}\n"

    return "\n".join(install_commands)

def build_customization(options: Dict[str, Any], output_mode: str) -> str:
    """
    Build the customization section of the script.
    
    Args:
        options: The selected options
        output_mode: The output mode (Quiet or Verbose)
        
    Returns:
        The customization commands as a string
    """
    customization_commands = []
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""

    try:
        nattd_data = load_nattd()
        
        if "customization" not in nattd_data or "apps" not in nattd_data["customization"]:
            return "# No customization options available\n"
            
        customization_apps = nattd_data["customization"]["apps"]
        
        if "customization" not in options:
            return "# No customization options selected\n"
        
        for app_id, app_value in options["customization"].items():
            if app_id not in customization_apps:
                continue
                
            app_data = customization_apps[app_id]
            
            # Handle apps with installation types (like Windows Fonts)
            if isinstance(app_value, dict) and app_value.get('selected', False):
                if 'installation_type' in app_value and 'installation_types' in app_data:
                    install_type = app_value['installation_type']
                    
                    if install_type not in app_data['installation_types']:
                        customization_commands.append(f"# Warning: Installation type {install_type} not found for {app_data.get('name', app_id)}")
                        continue
                        
                    commands = app_data['installation_types'][install_type].get('command', '')
                    app_name = app_data.get('name', app_id)
                    description = app_data.get('description', f"Installing {app_name}")
                    
                    customization_commands.append(f"# {description} ({install_type})")
                    customization_commands.append(f'color_echo "yellow" "Installing {app_name} ({install_type})..."')
                    
                    if isinstance(commands, list):
                        for cmd in commands:
                            customization_commands.append(f"{cmd}{quiet_redirect if should_quiet_redirect(cmd) else ''}")
                    else:
                        customization_commands.append(f"{commands}{quiet_redirect if should_quiet_redirect(commands) else ''}")
                    
                    customization_commands.append(f'color_echo "green" "{app_name} ({install_type}) installed successfully."')
                    customization_commands.append("")  # Add an empty line for readability
            
            # Handle apps without installation types
            elif app_value and 'command' in app_data:
                app_name = app_data.get('name', app_id)
                description = app_data.get('description', f"Installing {app_name}")
                
                customization_commands.append(f"# {description}")
                customization_commands.append(f'color_echo "yellow" "Installing {app_name}..."')
                
                commands = app_data['command']
                if isinstance(commands, list):
                    for cmd in commands:
                        customization_commands.append(f"{cmd}{quiet_redirect if should_quiet_redirect(cmd) else ''}")
                else:
                    customization_commands.append(f"{commands}{quiet_redirect if should_quiet_redirect(commands) else ''}")
                
                customization_commands.append(f'color_echo "green" "{app_name} installed successfully."')
                customization_commands.append("")  # Add an empty line for readability
    except Exception as e:
        logging.error(f"Error building customization: {str(e)}", exc_info=True)
        return f"# Error building customization: {str(e)}\n"

    return "\n".join(customization_commands)

def build_custom_script(options: Dict[str, Any], output_mode: str) -> str:
    """
    Build the custom script section of the script.
    
    Args:
        options: The selected options
        output_mode: The output mode (Quiet or Verbose)
        
    Returns:
        The custom script commands as a string
    """
    custom_script = options.get("custom_script", "").strip()
    if custom_script:
        return f"# Custom user-defined commands\n{custom_script}\n"
    return ""

def process_all_dependencies(options: Dict[str, Any], nattd_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Process all dependencies for all selected apps.
    
    Args:
        options: The selected options
        nattd_data: The NATTD configuration data
        
    Returns:
        Tuple containing:
        - Updated options with all dependencies resolved
        - List of notification messages about enabled dependencies
    """
    # Make a deep copy of options to avoid modifying the original
    updated_options = copy.deepcopy(options)
    all_notifications = []
    
    # First check system-level dependencies
    updated_options = check_dependencies(updated_options)
    
    # Process app-specific dependencies
    if "additional_apps" in updated_options and "additional_apps" in nattd_data:
        for category, category_data in updated_options["additional_apps"].items():
            if category not in nattd_data["additional_apps"]:
                continue
                
            for app_id, app_data in category_data.items():
                if not isinstance(app_data, dict) or not app_data.get('selected', False):
                    continue
                    
                if app_id not in nattd_data['additional_apps'][category]['apps']:
                    continue
                    
                app_config = nattd_data['additional_apps'][category]['apps'][app_id]
                if ('installation_types' in app_config and 
                    'installation_type' in app_data):
                    install_type = app_data['installation_type']
                    updated_options, notifications = process_installation_dependencies(app_config, install_type, updated_options)
                    all_notifications.extend(notifications)
    
    return updated_options, all_notifications

def build_script(options: Dict[str, Any], output_mode: str) -> str:
    """
    Build a preview of the script based on selected options.
    
    Args:
        options: The selected options
        output_mode: The output mode (Quiet or Verbose)
        
    Returns:
        A preview of the generated script
    """
    try:
        # Load NATTD data once
        nattd_data = load_nattd()
        
        # Process all dependencies first
        options, notifications = process_all_dependencies(options, nattd_data)
        
        script_parts = {
            "system_upgrade": build_system_upgrade(options, output_mode),
            "system_config": build_system_config(options, output_mode),
            "app_install": build_app_install(options, output_mode),
            "customization": build_customization(options, output_mode),
            "custom_script": build_custom_script(options, output_mode),
        }
        
        preview_script = "(...)  # Script header and initial setup\n\n"
        
        for placeholder, content in script_parts.items():
            if content and content.strip():  # Check if content is not None and not empty
                preview_script += f"# {placeholder.replace('_', ' ').title()}\n"
                preview_script += content + "\n\n"
        
        preview_script += "(...)  # Script footer"
        
        return preview_script
    except Exception as e:
        logging.error(f"Error building script preview: {str(e)}", exc_info=True)
        return f"# Error building script preview: {str(e)}\n# Please check the logs for more information."

def build_full_script(template: str, options: Dict[str, Any], output_mode: str) -> str:
    """
    Build the complete script based on the template and selected options.
    
    Args:
        template: The script template
        options: The selected options
        output_mode: The output mode (Quiet or Verbose)
        
    Returns:
        The complete generated script
    """
    try:
        # Load NATTD data once
        nattd_data = load_nattd()
        
        # Process all dependencies first
        options, notifications = process_all_dependencies(options, nattd_data)
        
        script_parts = {
            "system_upgrade": build_system_upgrade(options, output_mode),
            "system_config": build_system_config(options, output_mode),
            "app_install": build_app_install(options, output_mode),
            "customization": build_customization(options, output_mode),
            "custom_script": build_custom_script(options, output_mode),
        }
        
        # Create a copy of the template
        full_script = template
        
        for placeholder, content in script_parts.items():
            full_script = full_script.replace(f"{{{{{placeholder}}}}}", content)
        
        # Replace the hostname placeholder if it exists
        if "hostname" in options:
            full_script = full_script.replace("{hostname}", options["hostname"])
        else:
            # Use a default hostname if not provided
            full_script = full_script.replace("{hostname}", "fedora-workstation")
        
        return full_script
    except Exception as e:
        logging.error(f"Error building full script: {str(e)}", exc_info=True)
        error_script = "#!/bin/bash\n\n"
        error_script += f"echo \"Error building script: {str(e)}\"\n"
        error_script += "echo \"Please check the logs for more information.\"\n"
        return error_script
