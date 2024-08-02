PROFILES = {
    "Recommended": {
        "system_config": ["configure_dnf", "enable_dnf_autoupdate", "firmware_updates", "enable_rpmfusion", "configure_power_settings"],
        "essential_apps": ["install_mc", "install_bpytop", "install_rsync", "install_fastfetch", "install_unzip", "install_unrar", "install_git", "install_wget", "install_curl", "install_gnome_tweaks"],
        "additional_apps": {
            "internet_communication": ["install_vivaldi", "install_betterbird", "install_tor"],
            "office_productivity": ["install_libreoffice", "install_joplin", "install_freetube"],
            "media_graphics": ["install_vlc", "install_gimp", "install_inkscape"],
            "system_tools": ["install_mission_center", "install_extension_manager", "install_gear_lever"],
        },
        "customization": ["install_windows_fonts", "install_tela_icon_theme"],
        "custom_script": "echo Created with \u2764\ufe0f for Open Source",
        "installation_methods": {
            "gimp_install_method": "DNF",
            "vivaldi_install_method": "DNF",
            "inkscape_install_method": "DNF",
            "windows_fonts_method": "Microsoft Core Fonts"
        }
    }
}