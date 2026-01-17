import shutil
import subprocess
import os
import getpass

def run_debug():
    print(f"User: {getpass.getuser()}")
    print(f"Groups: {subprocess.check_output(['groups']).decode().strip()}")
    
    nmcli_path = shutil.which("nmcli")
    print(f"nmcli path: {nmcli_path}")
    
    if not nmcli_path:
        print("ERROR: nmcli not found in PATH")
        return

    print("\n--- Testing Scan (nmcli dev wifi) ---")
    try:
        # Run exactly what the service runs
        cmd = [nmcli_path, "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Command Failed (Code {result.returncode})")
            print(f"Stderr: {result.stderr}")
        else:
            print("Success! Output (first 5 lines):")
            lines = result.stdout.split('\n')
            for line in lines[:5]:
                print(line)
            print(f"... ({len(lines)} lines total)")
            
    except Exception as e:
        print(f"Exception running nmcli: {e}")

    print("\n--- Testing Status (nmcli general status) ---")
    try:
        subprocess.run([nmcli_path, "general", "status"], check=False)
    except:
        pass

if __name__ == "__main__":
    run_debug()
