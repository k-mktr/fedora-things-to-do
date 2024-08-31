import json
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO in production
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_nattd():
    with open('nattd.json', 'r') as f:
        return json.load(f)

def get_option_name(category: str, option: str) -> str:
    nattd_data = load_nattd()
    logging.debug(f"get_option_name - category: {category}, option: {option}")
    if category == "system_config":
        return nattd_data[category][option]["name"]
    elif category in ["essential_apps", "additional_apps"]:
        return nattd_data[category]["apps"][option]["name"]
    elif category == "customization":
        return nattd_data[category]["apps"][option]["name"]
    else:
        raise ValueError(f"Unknown category: {category}")

def get_option_description(category: str, option: str) -> str:
    nattd_data = load_nattd()
    logging.debug(f"get_option_description - category: {category}, option: {option}")
    if category == "system_config":
        return nattd_data[category][option]["description"]
    elif category in ["essential_apps", "additional_apps"]:
        return nattd_data[category]["apps"][option]["description"]
    elif category == "customization":
        return nattd_data[category]["apps"][option]["description"]
    else:
        raise ValueError(f"Unknown category: {category}")

def generate_options():
    nattd_data = load_nattd()
    logging.debug(f"generate_options - nattd_data: {nattd_data}")
    options = {
        "system_config": [key for key in nattd_data["system_config"].keys() if key != "description"],
        "essential_apps": [app["name"] for app in nattd_data["essential_apps"]["apps"]],
        "additional_apps": {},
        "customization": list(nattd_data["customization"]["apps"].keys())
    }
    
    for category, data in nattd_data["additional_apps"].items():
        options["additional_apps"][category] = {
            "name": data["name"],
            "apps": list(data["apps"].keys())
        }
    
    logging.debug(f"generate_options - options: {options}")
    return options

def build_system_upgrade(options: Dict[str, Any], output_mode: str) -> str:
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""
    
    upgrade_commands = [
        "log_message \"Performing system upgrade... This may take a while...\"",
        f"dnf upgrade -y{quiet_redirect}",
        ""  # Add an empty line for readability
    ]
    
    return "\n".join(upgrade_commands)

def should_quiet_redirect(cmd: str) -> bool:
    no_redirect_patterns = [
        "log_message",
        "echo",
        "printf",
        "read",
        "prompt_",
        "EOF"
    ]
    # Check if the command starts with any of the patterns or contains "EOF"
    return not any(cmd.startswith(pattern) or "EOF" in cmd for pattern in no_redirect_patterns)

# Add this function to check dependencies
def check_dependencies(options: Dict[str, Any]) -> Dict[str, Any]:
    nattd_data = load_nattd()
    
    # Check if multimedia codecs or GPU codecs are selected
    if any([
        options["system_config"].get("install_multimedia_codecs", False),
        options["system_config"].get("install_intel_codecs", False),
        options["system_config"].get("install_amd_codecs", False)
    ]):
        # Ensure RPM Fusion is enabled
        options["system_config"]["enable_rpmfusion"] = True
    
    return options

# Modify the build_system_config function
def build_system_config(options: Dict[str, Any], output_mode: str) -> str:
    # Check dependencies before building the config
    options = check_dependencies(options)
    config_commands = []
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""

    nattd_data = load_nattd()
    system_config = nattd_data["system_config"]

    for option, enabled in options["system_config"].items():
        if enabled and option in system_config:
            description = system_config[option]["description"]
            config_commands.append(f"# {description}")
            commands = system_config[option]["command"]
            if isinstance(commands, list):
                for cmd in commands:
                    if option == "set_hostname" and "hostnamectl set-hostname" in cmd:
                        cmd = f"{cmd} {{hostname}}"  # Use a placeholder for the hostname
                    if output_mode == "Quiet" and should_quiet_redirect(cmd):
                        cmd += quiet_redirect
                    config_commands.append(cmd)
            else:
                cmd = commands
                if option == "set_hostname" and "hostnamectl set-hostname" in cmd:
                    cmd = f"{cmd} {{hostname}}"  # Use a placeholder for the hostname
                if output_mode == "Quiet" and should_quiet_redirect(cmd):
                    cmd += quiet_redirect
                config_commands.append(cmd)
            config_commands.append("")  # Add an empty line for readability

    return "\n".join(config_commands)

def build_app_install(options: Dict[str, Any], output_mode: str) -> str:
    nattd_data = load_nattd()
    install_commands = []
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""

    # Essential apps
    essential_apps = [app for app in nattd_data["essential_apps"]["apps"] if options["essential_apps"].get(app["name"], False)]
    if essential_apps:
        install_commands.append("# Install essential applications")
        app_names = " ".join([app["name"] for app in essential_apps])
        install_commands.append(f"log_message \"Installing essential applications...\"")
        install_commands.append(f"dnf install -y {app_names}{quiet_redirect}")
        install_commands.append(f"log_message \"Essential applications installed successfully.\"")
        install_commands.append("")

    # Additional apps
    for category, category_data in options["additional_apps"].items():
        category_apps = [app_id for app_id, app_data in category_data.items() if app_data.get('selected', False)]
        if category_apps:
            install_commands.append(f"# Install {nattd_data['additional_apps'][category]['name']} applications")
            for app_id in category_apps:
                app_data = nattd_data['additional_apps'][category]['apps'][app_id]
                install_commands.append(f"log_message \"Installing {app_data['name']}...\"")
                if 'installation_types' in app_data and options["additional_apps"][category][app_id].get('installation_type'):
                    install_type = options["additional_apps"][category][app_id]['installation_type']
                    commands = app_data['installation_types'][install_type]['command']
                else:
                    commands = app_data["command"]
                
                if isinstance(commands, list):
                    for cmd in commands:
                        install_commands.append(f"{cmd}{quiet_redirect if should_quiet_redirect(cmd) else ''}")
                else:
                    install_commands.append(f"{commands}{quiet_redirect if should_quiet_redirect(commands) else ''}")
                install_commands.append(f"log_message \"{app_data['name']} installed successfully.\"")
                if app_id == "install_docker":
                    install_commands.append("# Note: Docker group changes will take effect after logging out and back in")
            install_commands.append("")

    return "\n".join(install_commands)

def build_customization(options: Dict[str, Any], output_mode: str) -> str:
    nattd_data = load_nattd()
    customization_commands = []
    quiet_redirect = " > /dev/null 2>&1" if output_mode == "Quiet" else ""

    customization_apps = nattd_data["customization"]["apps"]
    
    for app_id, app_data in customization_apps.items():
        if isinstance(options["customization"].get(app_id), dict):
            # This is for apps with installation types (like Windows Fonts)
            if options["customization"][app_id]['selected']:
                install_type = options["customization"][app_id]['installation_type']
                commands = app_data['installation_types'][install_type]['command']
                customization_commands.append(f"# {app_data['description']} ({install_type})")
                customization_commands.append(f"log_message \"Installing {app_data['name']} ({install_type})...\"")
                
                if isinstance(commands, list):
                    for cmd in commands:
                        customization_commands.append(f"{cmd}{quiet_redirect if should_quiet_redirect(cmd) else ''}")
                else:
                    customization_commands.append(f"{commands}{quiet_redirect if should_quiet_redirect(commands) else ''}")
                
                customization_commands.append(f"log_message \"{app_data['name']} ({install_type}) installed successfully.\"")
                customization_commands.append("")  # Add an empty line for readability
        elif options["customization"].get(app_id, False):
            # This is for apps without installation types
            customization_commands.append(f"# {app_data['description']}")
            customization_commands.append(f"log_message \"Installing {app_data['name']}...\"")
            
            if isinstance(app_data['command'], list):
                for cmd in app_data['command']:
                    customization_commands.append(f"{cmd}{quiet_redirect if should_quiet_redirect(cmd) else ''}")
            else:
                customization_commands.append(f"{app_data['command']}{quiet_redirect if should_quiet_redirect(app_data['command']) else ''}")
            
            customization_commands.append(f"log_message \"{app_data['name']} installed successfully.\"")
            customization_commands.append("")  # Add an empty line for readability

    return "\n".join(customization_commands)

def build_custom_script(options: Dict[str, Any], output_mode: str) -> str:
    custom_script = options.get("custom_script", "").strip()
    if custom_script:
        return f"# Custom user-defined commands\n{custom_script}\n"
    return ""