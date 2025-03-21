import streamlit as st
from utils import safely_load_file, AppState
from scripts import build_script, build_full_script

def render_header():
    """
    Render the application header with logo and title.
    """
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
    </style>
    <div class="header-container">
        <img src="https://fedoraproject.org/assets/images/fedora-workstation-logo.png" alt="Fedora Logo" class="logo">
        <h1 class="main-header">Not Another <i>'Things To Do'!</i></h1>
        <h3 class="sub-header">Initial System Setup Shell Script Builder for Fedora Workstation</h3>
    </div>
    """, unsafe_allow_html=True)

def render_script_preview():
    """
    Render the script preview section.
    """
    app_state = AppState.get_instance()
    options = app_state.get_options()
    output_mode = app_state.output_mode
    
    script_preview = st.empty()
    try:
        updated_script = build_script(options, output_mode)
        script_preview.code(updated_script, language="bash")
    except Exception as e:
        st.error(f"Error generating script preview: {str(e)}")
        script_preview.code("# Error generating script preview", language="bash")
    
    return script_preview

def render_build_button():
    """
    Render the build script button and handle script generation.
    """
    app_state = AppState.get_instance()
    
    if st.button("Build Your Script"):
        template = safely_load_file('template.sh', "#!/bin/bash\necho 'Error loading template'")
        options = app_state.get_options()
        output_mode = app_state.output_mode
        
        try:
            full_script = build_full_script(template, options, output_mode)
            app_state.set_full_script(full_script)
            app_state.set_script_built(True)
            st.success("Script built successfully!")
        except Exception as e:
            st.error(f"Error building script: {str(e)}")

def render_download_section():
    """
    Render the download section if a script has been built.
    """
    app_state = AppState.get_instance()
    
    if app_state.script_built:
        st.download_button(
            label="Download Your Script",
            data=app_state.full_script,
            file_name="fedora_things_to_do.sh",
            mime="text/plain"
        )
        
        st.markdown("""
        ### Your Script Has Been Created!

        Follow these steps to use your script:

        1. **Download the Script**: Click the 'Download Your Script' button above to save the script to your computer.

        2. **Make the Script Executable**: Open a terminal, navigate to the directory containing the downloaded script, and run:
           ```
           chmod +x fedora_things_to_do.sh
           ```

        3. **Run the Script**: Execute the script with sudo privileges:
           ```
           sudo ./fedora_things_to_do.sh
           ```

        ⚠️ **Caution**: This script will make changes to your system. Please review the script contents before running and ensure you understand the modifications it will make.
        """)

        st.markdown("""
        ### Optional Bonus Scripts
        
        If you want to further customize your system, you can find a "Bonus Scripts" section in the sidebar. This section includes additional standalone scripts that are not mandatory but can be useful for extra customization. The scripts available are:
        
        - **NVIDIA Drivers Script**: Installs NVIDIA drivers. It's recommended to run this script after performing a full system upgrade and rebooting your system.
        - **File Templates Script**: Creates a set of commonly used file templates in your home directory.
        
        If you decide to use these scripts, follow these steps:
        1. Download the desired script from the sidebar.
        2. Make it executable: `chmod +x script_name.sh`
        3. Run it: `./script_name.sh` (or with sudo if required)
        
        **Important**: These scripts are optional and should be run after completing the main setup and rebooting your system.
        """)

def render_main_panel():
    """
    Render the main panel of the application.
    """
    # Get app state and check for notifications
    app_state = AppState.get_instance()
    
    # Display any dependency notifications in the sidebar
    for notification in app_state.dependency_notifications:
        st.sidebar.info(notification)
    
    render_header()
    render_script_preview()
    render_build_button()
    render_download_section() 