#!/bin/bash
# System Cleanup Script for Fedora Workstation

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
LOG_FILE="/var/log/system_cleanup.log"

# Function to generate timestamps
get_timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

# Function to handle errors
handle_error() {
    local exit_code=$?
    local message="$1"
    if [ $exit_code -ne 0 ]; then
        color_echo "red" "ERROR: $message"
        exit $exit_code
    fi
}

echo "";
echo "╔═══════════════════════════════════════════════════════════════╗";
echo "║                                                               ║";
echo "║   ███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗       ║";
echo "║   ██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████║       ║";
echo "║   ███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║       ║";
echo "║   ╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║       ║";
echo "║   ███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║       ║";
echo "║   ╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝       ║";
echo "║                                                               ║";
echo "║   ██████╗██╗     ███████╗ █████╗ ███╗   ██╗██╗   ██╗██████╗   ║";
echo "║  ██╔════╝██║     ██╔════╝██╔══██╗████╗  ██║██║   ██║██╔══██╗  ║";
echo "║  ██║     ██║     █████╗  ███████║██╔██╗ ██║██║   ██║██████╔╝  ║";
echo "║  ██║     ██╔══╝  ██╔══╝  ██╔══██║██║╚██╗██║██║   ██║██╔═══╝   ║";
echo "║  ╚██████╗███████╗███████╗██║  ██║██║ ╚████║╚██████╔╝██║       ║";
echo "║   ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝       ║";
echo "║                                                               ║";
echo "╚═══════════════════════════════════════════════════════════════╝";
echo "";
echo "This script performs various system cleanup tasks on Fedora Workstation"
echo ""

# Function to remove old kernels
remove_old_kernels() {
    color_echo "yellow" "Removing old kernels..."
    # Get the current kernel version
    current_kernel=$(uname -r | sed 's/-.*//g')
    # List all installed kernels, sort them, and keep only the version numbers
    installed_kernels=$(rpm -q kernel --qf '%{VERSION}-%{RELEASE}\n' | sort -V | sed 's/-.*//g')
    # Count the number of installed kernels
    kernel_count=$(echo "$installed_kernels" | wc -l)

    if [ $kernel_count -le 2 ]; then
        color_echo "blue" "There are 2 or fewer kernels installed. No kernels will be removed."
        return 0
    fi

    # Get the list of kernels to remove (excluding the current and the latest)
    kernels_to_remove=$(echo "$installed_kernels" | head -n -2)

    for kernel in $kernels_to_remove; do
        if [ "$kernel" != "$current_kernel" ]; then
            color_echo "yellow" "Removing kernel $kernel"
            dnf remove -y kernel-$kernel kernel-core-$kernel kernel-modules-$kernel kernel-modules-extra-$kernel
            handle_error "Failed to remove kernel $kernel"
        fi
    done

    color_echo "green" "Old kernel removal completed."
}

# Function to clear DNF cache
clear_dnf_cache() {
    color_echo "yellow" "Clearing DNF cache..."
    dnf clean all
    handle_error "Failed to clear DNF cache"
}

# Function to remove orphaned packages
remove_orphaned_packages() {
    color_echo "yellow" "Removing orphaned packages..."
    dnf autoremove -y
    handle_error "Failed to remove orphaned packages"
}

# Function to clear user cache
clear_user_cache() {
    color_echo "yellow" "Clearing user cache..."
    if [ -d "$ACTUAL_HOME/.cache" ]; then
        find "$ACTUAL_HOME/.cache" -type f -delete
        find "$ACTUAL_HOME/.cache" -type d -empty -delete
    fi
    handle_error "Failed to clear user cache"
}

# Function to clear systemd journal logs
clear_journal_logs() {
    color_echo "yellow" "Clearing systemd journal logs..."
    journalctl --vacuum-time=7d
    handle_error "Failed to clear systemd journal logs"
}

# Function to clear temporary files
clear_temp_files() {
    color_echo "yellow" "Clearing temporary files..."
    rm -rf /tmp/*
    handle_error "Failed to clear temporary files"
}

# Function to update the system
update_system() {
    color_echo "blue" "Updating the system..."
    dnf upgrade -y
    handle_error "Failed to update the system"
}

# Main menu
while true; do
    echo ""
    echo "Please choose a cleanup option:"
    echo "1) Remove old kernels"
    echo "2) Clear DNF cache"
    echo "3) Remove orphaned packages"
    echo "4) Clear user cache"
    echo "5) Clear systemd journal logs"
    echo "6) Clear temporary files"
    echo "7) Update system"
    echo "8) Perform all cleanup tasks"
    echo "9) Exit"
    read -p "Enter your choice (1-9): " choice

    case $choice in
        1) remove_old_kernels ;;
        2) clear_dnf_cache ;;
        3) remove_orphaned_packages ;;
        4) clear_user_cache ;;
        5) clear_journal_logs ;;
        6) clear_temp_files ;;
        7) update_system ;;
        8)
            remove_old_kernels
            clear_dnf_cache
            remove_orphaned_packages
            clear_user_cache
            clear_journal_logs
            clear_temp_files
            update_system
            ;;
        9) 
            color_echo "blue" "Exiting system cleanup script."
            exit 0
            ;;
        *)
            color_echo "red" "Invalid option. Please try again."
            ;;
    esac
done
