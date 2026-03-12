import paramiko

HOST = "192.168.0.11"
USER = "tahmidrashid"
PASS = "shomik1A!!"
REMOTE_DIR = "/home/tahmidrashid/ReviewerDashboard"

def check():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USER, password=PASS)
        stdin, stdout, stderr = ssh.exec_command(f"cat {REMOTE_DIR}/app.log")
        print(stdout.read().decode())
        
        # Check if the process is running
        stdin, stdout, stderr = ssh.exec_command("pgrep -f 'python3 main.py'")
        pid = stdout.read().decode().strip()
        if pid:
            print(f"---\nProcess is RUNNING with PID: {pid}")
        else:
            print("---\nProcess is NOT RUNNING.")
    except Exception as e:
        print(f"Error checking logs: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    check()
