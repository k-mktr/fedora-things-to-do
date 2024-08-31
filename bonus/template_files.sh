#!/bin/bash
# File Templates Creation Script for Fedora Workstation

# Set variables
ACTUAL_USER=$SUDO_USER
ACTUAL_HOME=$(eval echo ~$SUDO_USER)
TEMPLATES_DIR="$ACTUAL_HOME/Templates"
LOG_FILE="/var/log/fedora_file_templates.log"

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

# Function to create a template file
create_template() {
    local filename="$1"
    local extension="${filename##*.}"
    local fullpath="$TEMPLATES_DIR/$filename"
    
    # Create the file
    touch "$fullpath"
    handle_error "Failed to create $filename"
    
    # Add some basic content based on file type
    case "$extension" in
        txt)
            echo "This is a text file template." > "$fullpath"
            ;;
        md)
            echo "# Markdown Template" > "$fullpath"
            echo "" >> "$fullpath"
            echo "## Section 1" >> "$fullpath"
            echo "" >> "$fullpath"
            echo "Your content here." >> "$fullpath"
            ;;
        html)
            echo "<!DOCTYPE html>" > "$fullpath"
            echo "<html lang=\"en\">" >> "$fullpath"
            echo "<head>" >> "$fullpath"
            echo "    <meta charset=\"UTF-8\">" >> "$fullpath"
            echo "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">" >> "$fullpath"
            echo "    <title>Document</title>" >> "$fullpath"
            echo "</head>" >> "$fullpath"
            echo "<body>" >> "$fullpath"
            echo "    " >> "$fullpath"
            echo "</body>" >> "$fullpath"
            echo "</html>" >> "$fullpath"
            ;;
        css)
            echo "/* CSS Template */" > "$fullpath"
            echo "" >> "$fullpath"
            echo "body {" >> "$fullpath"
            echo "    font-family: Arial, sans-serif;" >> "$fullpath"
            echo "    margin: 0;" >> "$fullpath"
            echo "    padding: 0;" >> "$fullpath"
            echo "}" >> "$fullpath"
            ;;
        js)
            echo "// JavaScript Template" > "$fullpath"
            echo "" >> "$fullpath"
            echo "document.addEventListener('DOMContentLoaded', function() {" >> "$fullpath"
            echo "    // Your code here" >> "$fullpath"
            echo "});" >> "$fullpath"
            ;;
        py)
            echo "#!/usr/bin/env python3" > "$fullpath"
            echo "# -*- coding: utf-8 -*-" >> "$fullpath"
            echo "" >> "$fullpath"
            echo "def main():" >> "$fullpath"
            echo "    pass" >> "$fullpath"
            echo "" >> "$fullpath"
            echo "if __name__ == \"__main__\":" >> "$fullpath"
            echo "    main()" >> "$fullpath"
            ;;
        sh)
            echo "#!/bin/bash" > "$fullpath"
            echo "" >> "$fullpath"
            echo "# Your script here" >> "$fullpath"
            ;;
        sql)
            echo "-- SQL Template" > "$fullpath"
            echo "" >> "$fullpath"
            echo "SELECT * FROM table_name;" >> "$fullpath"
            ;;
        xml)
            echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" > "$fullpath"
            echo "<root>" >> "$fullpath"
            echo "    <element>Content</element>" >> "$fullpath"
            echo "</root>" >> "$fullpath"
            ;;
        json)
            echo "{" > "$fullpath"
            echo "    \"key\": \"value\"" >> "$fullpath"
            echo "}" >> "$fullpath"
            ;;
        yml|yaml)
            echo "---" > "$fullpath"
            echo "key: value" >> "$fullpath"
            ;;
        tex)
            echo "\documentclass{article}" > "$fullpath"
            echo "\begin{document}" >> "$fullpath"
            echo "Your LaTeX content here." >> "$fullpath"
            echo "\end{document}" >> "$fullpath"
            ;;
        *)
            # For other file types, just leave them empty
            ;;
    esac
    
    log_message "Created template: $filename"
}

echo "";
echo "╔═══════════════════════════════════════════════════════════════════════════════════╗";
echo "║                                                                                   ║";
echo "║   ████████╗███████╗███╗   ███╗██████╗ ██╗      █████╗ ████████╗███████╗███████╗   ║";
echo "║   ╚══██╔══╝██╔════╝████╗ ████║██╔══██╗██║     ██╔══██╗╚══██╔══╝██╔════╝██╔════╝   ║";
echo "║      ██║   █████╗  ██╔████╔██║██████╔╝██║     ███████║   ██║   █████╗  ███████╗   ║";
echo "║      ██║   ██╔══╝  ██║╚██╔╝██║██╔═══╝ ██║     ██╔══██║   ██║   ██╔══╝  ╚════██║   ║";
echo "║      ██║   ███████╗██║ ╚═╝ ██║██║     ███████╗██║  ██║   ██║   ███████╗███████║   ║";
echo "║      ╚═╝   ╚══════╝╚═╝     ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚══════╝   ║";
echo "║                                                                                   ║";
echo "╚═══════════════════════════════════════════════════════════════════════════════════╝";
echo "";
echo "This script creates file templates in your Templates directory."
echo "These templates will appear in the 'New Document' menu when you right-click"
echo "in the GNOME Files app, allowing you to quickly create new files with"
echo "predefined structures. It's a handy feature to streamline your workflow!"
echo "";
echo "Available templates:"

# List of template files
templates=(
    "text_document.txt"
    "markdown_document.md"
    "spreadsheet.ods"
    "presentation.odp"
    "document.odt"
    "html_page.html"
    "css_stylesheet.css"
    "javascript_file.js"
    "python_script.py"
    "bash_script.sh"
    "sql_query.sql"
    "xml_file.xml"
    "json_file.json"
    "yaml_file.yml"
    "latex_document.tex"
    "c_source.c"
    "cpp_source.cpp"
    "java_source.java"
    "ruby_script.rb"
    "php_script.php"
    "makefile"
    "readme.md"
    "license.txt"
    "docker_compose.yml"
    "dockerfile"
)

# Display templates with numbers
for i in "${!templates[@]}"; do
    echo "$((i+1)). ${templates[$i]}"
done

echo ""
echo "Enter the numbers of the templates you want to create (space-separated),"
echo "or press Enter to create all templates."
read -p "Your choice: " choices

# Create the Templates directory if it doesn't exist
mkdir -p "$TEMPLATES_DIR"
handle_error "Failed to create Templates directory"

if [ -z "$choices" ]; then
    # Create all templates
    for template in "${templates[@]}"; do
        create_template "$template"
    done
else
    # Create selected templates
    for choice in $choices; do
        if [ "$choice" -ge 1 ] && [ "$choice" -le "${#templates[@]}" ]; then
            create_template "${templates[$((choice-1))]}"
        else
            log_message "Invalid choice: $choice"
        fi
    done
fi

log_message "File templates creation completed."
echo "File templates have been created in $TEMPLATES_DIR"