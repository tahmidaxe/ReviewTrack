import paramiko

HOST = "192.168.0.11"
USER = "tahmidrashid"
PASS = "shomik1A!!"
REMOTE_DIR = "/home/tahmidrashid/ReviewerDashboard"
DESKTOP_DIR = "/home/tahmidrashid/Desktop"

DESKTOP_FILE_CONTENT = f"""[Desktop Entry]
Name=ReviewTrack
Comment=Launch the Paper Review Dashboard
Exec=/bin/sh -c "export DISPLAY=:0 && cd {REMOTE_DIR} && python3 main.py"
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
"""

def create_shortcut():
    print(f"Connecting to {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, username=USER, password=PASS)
        print("Connected. Creating desktop shortcut...")
        
        # Ensure Desktop directory exists (it usually does, but just in case)
        ssh.exec_command(f"mkdir -p {DESKTOP_DIR}")
        
        # Create the .desktop file
        shortcut_path = f"{DESKTOP_DIR}/ReviewTrack.desktop"
        
        # Write the file content
        sftp = ssh.open_sftp()
        with sftp.file(shortcut_path, 'w') as f:
            f.write(DESKTOP_FILE_CONTENT)
        sftp.close()
        
        # Make it executable and trusted (needed for LXDE/Desktop environments)
        ssh.exec_command(f"chmod +x {shortcut_path}")
        
        print("Desktop icon created successfully! You can now launch it from the Pi's desktop.")
        
    except Exception as e:
        print(f"Failed to create shortcut: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    create_shortcut()
