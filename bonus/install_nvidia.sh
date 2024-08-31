#!/bin/bash
# NVIDIA Driver Installation Script for Fedora Workstation

# Check if the script is run with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo"
    exit 1
fi

# Set variables
ACTUAL_USER=$SUDO_USER
ACTUAL_HOME=$(eval echo ~$SUDO_USER)
LOG_FILE="/var/log/nvidia_driver_installation.log"

# Function to generate timestamps
get_timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

# Function to log messages
log_message() {
    local message="$1"
    echo "$(get_timestamp) - $message" | tee -a "$LOG_FILE"
}

# Function to handle errors
handle_error() {
    local exit_code=$?
    local message="$1"
    if [ $exit_code -ne 0 ]; then
        log_message "ERROR: $message"
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
        log_message "RPM Fusion method selected"
        
        # Add RPM Fusion repositories
        log_message "Adding RPM Fusion repositories..."
        dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
        dnf install -y https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
        handle_error "Failed to add RPM Fusion repositories"

        # Update the system
        log_message "Updating the system..."
        dnf update -y
        handle_error "Failed to update the system"

        # Install NVIDIA drivers
        log_message "Installing NVIDIA drivers..."
        dnf install -y akmod-nvidia
        handle_error "Failed to install NVIDIA drivers"

        # Install CUDA (optional)
        read -p "Do you want to install CUDA? (y/n): " install_cuda
        if [[ $install_cuda =~ ^[Yy]$ ]]; then
            log_message "Installing CUDA..."
            dnf install -y cuda
            handle_error "Failed to install CUDA"
        fi
        ;;
    2)
        log_message "NVIDIA official .run file method selected"
        
        # Install necessary packages
        log_message "Installing necessary packages..."
        dnf install -y kernel-devel kernel-headers gcc make dkms acpid libglvnd-glx libglvnd-opengl libglvnd-devel pkgconfig
        handle_error "Failed to install necessary packages"

        # Download the latest NVIDIA driver
        log_message "Downloading the latest NVIDIA driver..."
        driver_url=$(curl -s https://www.nvidia.com/Download/processFind.aspx?psid=101&pfid=816&osid=12&lid=1&whql=1&lang=en-us&ctk=0 | grep -o 'https://[^"]*' | grep '.run' | head -n 1)
        wget $driver_url -O /tmp/nvidia_driver.run
        handle_error "Failed to download NVIDIA driver"

        # Stop the display manager
        log_message "Stopping the display manager..."
        systemctl isolate multi-user.target
        handle_error "Failed to stop the display manager"

        # Install the NVIDIA driver
        log_message "Installing the NVIDIA driver..."
        bash /tmp/nvidia_driver.run --silent
        handle_error "Failed to install NVIDIA driver"

        # Start the display manager
        log_message "Starting the display manager..."
        systemctl isolate graphical.target
        handle_error "Failed to start the display manager"
        ;;
    *)
        log_message "Invalid choice. Exiting."
        exit 1
        ;;
esac

log_message "NVIDIA driver installation completed."
echo "Installation complete. Please reboot your system to apply changes."
read -p "Do you want to reboot now? (y/n): " reboot_choice
if [[ $reboot_choice =~ ^[Yy]$ ]]; then
    log_message "Rebooting the system..."
    reboot
else
    log_message "Reboot postponed. Please remember to reboot your system to complete the installation."
fi