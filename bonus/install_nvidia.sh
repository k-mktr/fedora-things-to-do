#!/bin/bash
# NVIDIA Driver Installation Script for Fedora Workstation

# Check if the script is run with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo"
    exit 1
fi

# Funtion to echo colored text
color_echo() {
    local color="$1"
    local text="$2"
    case "$color" in
        "red")     echo -e "\033[0;31m$text\033[0m" ;;
        "green")   echo -e "\033[0;32m$text\033[0m" ;;
        "yellow")  echo -e "\033[1;33m$text\033[0m" ;;
        "blue")    echo -e "\033[0;34m$text\033[0m" ;;
        *)         echo "$text" ;;
    esac
}

# Set variables
ACTUAL_USER=$SUDO_USER
ACTUAL_HOME=$(eval echo ~$SUDO_USER)
LOG_FILE="/var/log/nvidia_driver_installation.log"

# Function to generate timestamps
get_timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

# Function to handle errors
handle_error() {
    local exit_code=$?
    local message="$1"
    if [ $exit_code -ne 0 ]; then
        color_echo \"red\" "ERROR: $message"
        exit $exit_code
    fi
}

echo "";
echo "╔══════════════════════════════════════════════════════════╗";
echo "║                                                          ║";
echo "║   ███╗   ██╗██╗   ██╗██╗██████╗ ██╗ █████╗               ║";
echo "║   ████╗  ██║██║   ██║██║██╔══██╗██║██╔══██╗              ║";
echo "║   ██╔██╗ ██║██║   ██║██║██║  ██║██║███████║              ║";
echo "║   ██║╚██╗██║╚██╗ ██╔╝██║██║  ██║██║██╔══██║              ║";
echo "║   ██║ ╚████║ ╚████╔╝ ██║██████╔╝██║██║  ██║              ║";
echo "║   ╚═╝  ╚═══╝  ╚═══╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝              ║";
echo "║                                                          ║";
echo "║   ██████╗ ██████╗ ██╗██╗   ██╗███████╗██████╗ ███████╗   ║";
echo "║   ██╔══██╗██╔══██╗██║██║   ██║██╔════╝██╔══██╗██╔════╝   ║";
echo "║   ██║  ██║██████╔╝██║██║   ██║█████╗  ██████╔╝███████╗   ║";
echo "║   ██║  ██║██╔══██╗██║╚██╗ ██╔╝██╔══╝  ██╔══██╗╚════██║   ║";
echo "║   ██████╔╝██║  ██║██║ ╚████╔╝ ███████╗██║  ██║███████║   ║";
echo "║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝   ║";
echo "║                                                          ║";
echo "╚══════════════════════════════════════════════════════════╝";
echo "";
echo "This script installs NVIDIA drivers on Fedora Workstation"
echo ""
echo "IMPORTANT: This script should be run outside of the graphical user interface (GUI)."
echo "To access a bare terminal window:"
echo "1. Press Ctrl+Alt+F3 to switch to a virtual console."
echo "2. Log in with your username and password."
echo "3. Run this script with sudo."
echo "4. After installation, reboot your system"
echo ""
echo "If you're not comfortable with this process, please seek assistance from an experienced user."
echo ""
echo "Please choose the installation method:"
echo "1) RPM Fusion method (recommended)"
echo "2) NVIDIA official .run file method"
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        color_echo "blue" "RPM Fusion method selected"
        
        # Add RPM Fusion repositories
        color_echo "yellow" "Adding RPM Fusion repositories..."
        dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
        dnf install -y https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
        handle_error "Failed to add RPM Fusion repositories"

        # Update the system
        color_echo "yellow" "Updating the system..."
        dnf update -y
        handle_error "Failed to update the system"

        # Install NVIDIA drivers
        color_echo "yellow" "Installing NVIDIA drivers..."
        dnf install -y akmod-nvidia
        handle_error "Failed to install NVIDIA drivers"

        # Install CUDA (optional)
        read -p "Do you want to install CUDA? (y/n): " install_cuda
        if [[ $install_cuda =~ ^[Yy]$ ]]; then
            color_echo "yellow" "Installing CUDA..."
            dnf install -y xorg-x11-drv-nvidia-cuda
            handle_error "Failed to install CUDA"
        fi
        ;;
    2)
        color_echo "blue" "NVIDIA official .run file method selected"
        
        # Install necessary packages
        color_echo "yellow" "Installing necessary packages..."
        dnf install -y kernel-devel kernel-headers gcc make dkms acpid libglvnd-glx libglvnd-opengl libglvnd-devel pkgconfig
        handle_error "Failed to install necessary packages"

        # Download the latest NVIDIA driver
        color_echo "yellow" "Downloading the latest NVIDIA driver..."
        driver_url=$(curl -s https://www.nvidia.com/Download/processFind.aspx?psid=101&pfid=816&osid=12&lid=1&whql=1&lang=en-us&ctk=0 | grep -o 'https://[^"]*' | grep '.run' | head -n 1)
        wget $driver_url -O /tmp/nvidia_driver.run
        handle_error "Failed to download NVIDIA driver"

        # Stop the display manager
        color_echo "blue" "Stopping the display manager..."
        systemctl isolate multi-user.target
        handle_error "Failed to stop the display manager"

        # Install the NVIDIA driver
        color_echo "yellow" "Installing the NVIDIA driver..."
        bash /tmp/nvidia_driver.run --silent
        handle_error "Failed to install NVIDIA driver"

        # Start the display manager
        color_echo "blue" "Starting the display manager..."
        systemctl isolate graphical.target
        handle_error "Failed to start the display manager"
        ;;
    *)
        color_echo "red" "Invalid choice. Exiting."
        exit 1
        ;;
esac

color_echo "green" "NVIDIA driver installation completed."
echo "Installation complete. Please reboot your system to apply changes."
read -p "Do you want to reboot now? (y/n): " reboot_choice
if [[ $reboot_choice =~ ^[Yy]$ ]]; then
    color_echo "green" "Rebooting the system..."
    reboot
else
    color_echo "blue" "Reboot postponed. Please remember to reboot your system to complete the installation."
fi
