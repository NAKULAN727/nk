"""
Script to generate translation files for the project.
Run this script from the project root directory.
"""
import os
import subprocess

def main():
    # Make sure the locale directory exists
    os.makedirs('locale', exist_ok=True)
    
    # Generate .po file for Tamil
    subprocess.run(['django-admin', 'makemessages', '-l', 'ta'])
    
    print("Translation files generated. Edit the .po files in the locale directory.")
    print("After editing, run 'django-admin compilemessages' to compile the translations.")

if __name__ == "__main__":
    main()