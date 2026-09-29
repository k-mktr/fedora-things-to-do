"""Predefined configuration profiles for Fedora Workstation NATTD.

A profile is a curated, human-reviewed starting point. Applying one replaces
the current selection with the profile's contents (anything not in the profile
is unselected), so the result is predictable.

Profile format (keep ids in sync with nattd.json - CI validates this):

    PROFILES = {
        "Name": {
            "description": "what this profile is for",
            "system_config": ["<system_config key>", ...],
            "essential_apps": ["<essential app name>", ...],
            "additional_apps": {
                "<category>": [
                    "<app_id>",                                   # default install type
                    {"id": "<app_id>", "installation_type": "DNF"},  # explicit type
                ],
            },
            "customization": [
                "<app_id>",
                {"id": "<app_id>", "installation_type": "core"},
            ],
        },
    }
"""

import logging
from typing import Any, Dict

import streamlit as st

from utils import load_nattd


PROFILES: Dict[str, Dict[str, Any]] = {
    "Recommended": {
        "description": "A curated everyday-driver setup: DNF optimizations, core utilities, browser, office and media apps.",
        "system_config": [
            "configure_dnf",
            "enable_dnf_autoupdate",
            "firmware_updates",
            "configure_power_settings",
        ],
        "essential_apps": [
            "mc", "btop", "rsync", "fastfetch", "unzip", "unrar",
            "git", "wget", "curl", "gnome-tweaks",
        ],
        "additional_apps": {
            "internet_communication": ["install_vivaldi", "install_betterbird", "install_tor"],
            "office_productivity": ["install_libreoffice", "install_joplin"],
            "media_graphics": ["install_vlc", "install_gimp", "install_inkscape", "install_freetube"],
            "system_tools": ["install_mission_center", "install_extension_manager", "install_gear_lever"],
        },
        "customization": [
            {"id": "install_microsoft_fonts", "installation_type": "core"},
            "install_tela_icon_theme",
        ],
    },
}


def build_profile_options(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a profile definition into an options overlay (selections only).

    Pure function - no UI, no nattd.json access.

    Args:
        profile: A PROFILES entry.

    Returns:
        Overlay in the same shape as app options, containing only the
        profile's selections.
    """
    overlay: Dict[str, Any] = {
        "system_config": {},
        "essential_apps": {},
        "additional_apps": {},
        "customization": {},
    }

    for opt in profile.get("system_config", []):
        overlay["system_config"][opt] = True

    for name in profile.get("essential_apps", []):
        overlay["essential_apps"][name] = True

    for category, apps in profile.get("additional_apps", {}).items():
        overlay["additional_apps"][category] = {}
        for item in apps:
            if isinstance(item, str):
                overlay["additional_apps"][category][item] = {"selected": True}
            elif isinstance(item, dict) and "id" in item:
                entry: Dict[str, Any] = {"selected": True}
                if item.get("installation_type"):
                    entry["installation_type"] = item["installation_type"]
                overlay["additional_apps"][category][item["id"]] = entry

    for item in profile.get("customization", []):
        if isinstance(item, str):
            overlay["customization"][item] = True
        elif isinstance(item, dict) and "id" in item:
            entry = {"selected": True}
            if item.get("installation_type"):
                entry["installation_type"] = item["installation_type"]
            overlay["customization"][item["id"]] = entry

    return overlay


def build_full_options(overlay: Dict[str, Any], nattd_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expand an overlay into a complete options dict covering every nattd entry.

    Every selectable entry is present with an explicit on/off value, so applying
    a profile (or importing a saved selection) fully replaces the current state.
    Unknown ids in the overlay are skipped with a warning - this keeps stale
    profiles from crashing the app after nattd.json changes.

    Args:
        overlay: Partial options (a profile overlay or an imported selection).
        nattd_data: Loaded nattd.json.

    Returns:
        Complete options dict in the AppState shape.
    """
    options: Dict[str, Any] = {
        "system_config": {},
        "essential_apps": {},
        "additional_apps": {},
        "customization": {},
    }

    for opt, entry in nattd_data.get("system_config", {}).items():
        if isinstance(entry, dict) and "command" in entry:
            options["system_config"][opt] = bool(
                (overlay.get("system_config") or {}).get(opt, False))
    # suboptions ride along with configure_dnf when present in the overlay
    if "configure_dnf_suboptions" in (overlay.get("system_config") or {}):
        options["system_config"]["configure_dnf_suboptions"] = \
            overlay["system_config"]["configure_dnf_suboptions"]

    for app in nattd_data.get("essential_apps", {}).get("apps", []):
        name = app.get("name")
        if name:
            options["essential_apps"][name] = bool(
                (overlay.get("essential_apps") or {}).get(name, False))

    for category, category_data in nattd_data.get("additional_apps", {}).items():
        options["additional_apps"][category] = {}
        overlay_cat = (overlay.get("additional_apps") or {}).get(category, {})
        for app_id, app_config in category_data.get("apps", {}).items():
            ov = overlay_cat.get(app_id, {})
            selected = bool(ov.get("selected", False)) if isinstance(ov, dict) else bool(ov)
            entry: Dict[str, Any] = {"selected": selected}
            if selected and "installation_types" in app_config:
                itype = ov.get("installation_type") if isinstance(ov, dict) else None
                if itype and itype in app_config["installation_types"]:
                    entry["installation_type"] = itype
                else:
                    entry["installation_type"] = list(app_config["installation_types"].keys())[0]
            options["additional_apps"][category][app_id] = entry

    for app_id, app_config in nattd_data.get("customization", {}).get("apps", {}).items():
        ov = (overlay.get("customization") or {}).get(app_id, False)
        if isinstance(ov, dict):
            selected = bool(ov.get("selected", False))
        else:
            selected = bool(ov)
            ov = {}
        if selected and "installation_types" in app_config:
            itype = ov.get("installation_type")
            if itype and itype in app_config["installation_types"]:
                options["customization"][app_id] = {"selected": True, "installation_type": itype}
            else:
                options["customization"][app_id] = {
                    "selected": True,
                    "installation_type": list(app_config["installation_types"].keys())[0],
                }
        elif selected:
            options["customization"][app_id] = True
        else:
            options["customization"][app_id] = False

    # Warn about overlay ids that don't exist in nattd.json so stale profiles
    # don't silently lose selections after nattd.json changes
    unknown = []
    for category in list(options["additional_apps"].keys()):
        for app_id in (overlay.get("additional_apps") or {}).get(category, {}):
            if app_id not in options["additional_apps"][category]:
                unknown.append(f"{category}/{app_id}")
    for app_id in (overlay.get("customization") or {}):
        if app_id not in options["customization"]:
            unknown.append(f"customization/{app_id}")
    for opt in (overlay.get("system_config") or {}):
        if opt not in options["system_config"]:
            unknown.append(f"system_config/{opt}")
    if unknown:
        logging.warning(f"Profile/selection references unknown ids (ignored): {unknown}")

    return options


def sync_session_widgets(options: Dict[str, Any]) -> None:
    """
    Push option values into Streamlit widget session keys so the sidebar
    reflects the applied state on the next run (checkboxes are keyed, so a
    plain state change alone would be overwritten by the widgets).
    """
    for opt, value in (options.get("system_config") or {}).items():
        if isinstance(value, bool):
            st.session_state[f"system_config_{opt}"] = value

    for name, value in (options.get("essential_apps") or {}).items():
        if isinstance(value, bool):
            st.session_state[f"essential_app_{name}"] = value

    for category, apps in (options.get("additional_apps") or {}).items():
        for app_id, data in apps.items():
            selected = bool(data.get("selected", False)) if isinstance(data, dict) else bool(data)
            st.session_state[f"app_{category}_{app_id}"] = selected
            if selected and isinstance(data, dict) and data.get("installation_type"):
                st.session_state[f"{category}_{app_id}_install_type"] = data["installation_type"]

    for app_id, data in (options.get("customization") or {}).items():
        selected = bool(data.get("selected", False)) if isinstance(data, dict) else bool(data)
        st.session_state[f"customization_{app_id}"] = selected
        if selected and isinstance(data, dict) and data.get("installation_type"):
            st.session_state[f"customization_{app_id}_install_type"] = data["installation_type"]


def apply_profile(app_state: Any, profile_name: str) -> None:
    """Apply a predefined profile to the app state and sidebar widgets."""
    nattd_data = load_nattd()
    overlay = build_profile_options(PROFILES[profile_name])
    options = build_full_options(overlay, nattd_data)
    sync_session_widgets(options)
    app_state.update_options(options)


def apply_imported_selection(app_state: Any, imported: Dict[str, Any]) -> None:
    """Apply an exported selection (nattd-profile.json) to the app state."""
    nattd_data = load_nattd()
    options = build_full_options(imported, nattd_data)
    sync_session_widgets(options)

    hostname = imported.get("hostname")
    if hostname:
        st.session_state["hostname_input"] = hostname
    custom_script = imported.get("custom_script")
    if custom_script:
        st.session_state["custom_script_input"] = custom_script
        options["custom_script"] = custom_script

    app_state.update_options(options)
