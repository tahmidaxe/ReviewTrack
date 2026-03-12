import paramiko
import os
import time

HOST = "192.168.0.11"
USER = "tahmidrashid"
PASS = "shomik1A!!"
REMOTE_DIR = "/home/tahmidrashid/ReviewerDashboard"

def deploy():
    print(f"Connecting to {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(HOST, username=USER, password=PASS)
        print("Connected successfully.")
        
        # Make directory
        ssh.exec_command(f"mkdir -p {REMOTE_DIR}")
        
        print("Transferring files via SFTP...")
        sftp = ssh.open_sftp()
        
        files_to_transfer = [
            "main.py",
            "ui_components.py",
            "database.py",
            "styles.qss"
        ]
        
        for file in files_to_transfer:
            local_path = file
            remote_path = f"{REMOTE_DIR}/{file}"
            if os.path.exists(local_path):
                print(f"  Uploading {file}...")
                sftp.put(local_path, remote_path)
            else:
                print(f"  ERROR: {file} not found locally.")
                
        sftp.close()
        print("Files transferred.")
        
        # Run tests / Display app
        print("Setting up display and running app on Pi...")
        ssh.exec_command("export DISPLAY=:0 && python3 -m pip install PyQt6")
        time.sleep(5)  # Give it a bit to ensure it completes if already installed
        
        # Kill any existing main.py we uploaded
        ssh.exec_command("pkill -f 'python3 main.py'")
        
        # Start it in background and redirect output to a file we can read
        stdin, stdout, stderr = ssh.exec_command(f"export DISPLAY=:0 && cd {REMOTE_DIR} && nohup python3 main.py > app.log 2>&1 &")
        
        print("App should now be running on the Pi display!")
        print("To check logs, SSH in and run: tail -f ~/ReviewerDashboard/app.log")
        
    except Exception as e:
        print(f"Deployment failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy()
