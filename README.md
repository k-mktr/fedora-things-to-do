# Fedora Workstation "Not Yet Another Things To Do"!

![Fedora Workstation Setup](./cover.png)

**Fedora Workstation Initial System Setup Shell Script Builder**

## Overview

This project provides a Streamlit-based web application that allows users to generate a customized shell script for setting up a fresh Fedora Workstation installation. The application offers a user-friendly interface to select various system configurations, applications, and customization options.

## Features

- **System Configuration**: Set hostname, configure DNF, enable auto-updates, install SSH, check for firmware updates, and enable RPM Fusion repositories.
- **Essential Apps**: Install popular command-line tools and utilities with detailed descriptions.
- **Additional Apps**: Choose from a wide range of applications categorized by purpose:
  - Internet & Communication (browsers, email clients, messaging apps)
  - Office & Productivity
  - Media & Graphics
  - Gaming & Emulation
  - System Tools
  - Remote Access & Networking
  - File Sharing & Download
- **Customization**: 
  - Install fonts (Windows, Google, Adobe Source)
  - Install themes (e.g., Tela Icon Theme)
  - Configure power settings
  - Set up development environments (Zsh, Oh My Zsh, Miniconda)
- **Advanced Options**: Add custom shell commands to be included in the generated script.
- **Script Preview**: View a preview of the generated script before downloading.
- **One-Click Download**: Generate and download the customized script with a single click.
- **Output Mode Selection**: Choose between Quiet (hide command output) and Verbose (show full output) modes.

## Requirements

- Python 3.7+
- Streamlit
- A modern web browser

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/k-mktr/fedora-things-to-do.git
   cd fedora-workstation-setup
   ```

2. Install the required Python packages:
   ```
   pip install streamlit pip --upgrade
   ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`) or use [our official public instance](https://share.streamlit.io/k-mktr/fedora-things-to-do/main/app.py)

3. Use the sidebar to select your desired configuration options.

5. Choose the Output Mode (Quiet or Verbose) to control the level of detail in the generated script.

6. (Optional) Add custom shell commands in the Advanced section.

7. Click the "Build Your Script" button to create your customized script.

8. Review the script preview and click "Download Your Script" to save it.

9. Follow the instructions provided after generating the script to make it executable and run it on your Fedora system.

## Script Template

The `script_template.sh` file serves as the base for the generated script. It includes:

- Error handling and logging functionality
- User prompts for optional steps
- A modular structure that allows for easy customization

## Caution

The generated script will make system-wide changes. Always review the script contents before running it on your system.

## Contributing

Contributions are welcome! If you'd like to see additional apps or options included, please open an issue or submit a pull request. Here are some ways you can contribute:

- Suggest new applications or system configurations to include
- Report bugs or issues you encounter
- Enhance the user interface or add new features

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Fedora Project for their excellent Linux distribution
- Streamlit for their intuitive app framework
- All contributors of Open Source Software

## Contact

For questions, feedback, or support, please:
- Open an issue on this repository
- Contact the author: [Karol Stefan Danisz](https://mktr.sbs/linkedin)

## Roadmap

Future plans for this project include:
- ✅ Enhancing user experience with more intuitive interface options
- ✅ Adding Advanced Section for a custom Shell Commands
- Implementing predefined configuration Profiles
- Further organizing the code
- Implementing a feature to save and load custom profiles 
- Developing versions for other Linux distributions (e.g., Debian/Ubuntu)
- Adding more applications and configuration options

Created with ❤️ for Open Source