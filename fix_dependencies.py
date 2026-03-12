import paramiko
import time

HOST = "192.168.0.11"
USER = "tahmidrashid"
PASS = "shomik1A!!"
REMOTE_DIR = "/home/tahmidrashid/ReviewerDashboard"

def fix():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USER, password=PASS)
        print("Installing PyQt6 using apt-get...")
        
        # Need to use sudo with password
        sudo_command = f'echo "{PASS}" | sudo -S apt-get update && echo "{PASS}" | sudo -S apt-get install -y python3-pyqt6'
        
        stdin, stdout, stderr = ssh.exec_command(sudo_command)
        
        # We need to wait for apt-get to finish
        exit_status = stdout.channel.recv_exit_status()
        print(f"Apt-get finished with status {exit_status}")
        print("STDOUT:", stdout.read().decode())
        print("STDERR:", stderr.read().decode())
        
        print("Restarting app...")
        ssh.exec_command(f"export DISPLAY=:0 && cd {REMOTE_DIR} && nohup python3 main.py > app.log 2>&1 &")
        print("Launched app.")
        
    except Exception as e:
        print(f"Error fixing dependencies: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    fix()
