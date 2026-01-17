import shutil
import subprocess
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class WifiService:
    def __init__(self):
        self.nmcli_path = shutil.which("nmcli")
        self.mock_mode = self.nmcli_path is None
        if self.mock_mode:
            logger.warning("nmcli not found. Running in WiFi Mock Mode.")

    def scan_networks(self) -> List[Dict]:
        """Returns list of {ssid, signal, security}"""
        if self.mock_mode:
            return [{"ssid": "Mock Network", "signal": 100, "security": "WPA2"}]
        
        try:
            # 1. Ensure WiFi is on
            import time
            subprocess.run([self.nmcli_path, "radio", "wifi", "on"], check=False)
            time.sleep(5)
            
            # 2. Run nmcli
            cmd = [self.nmcli_path, "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list", "--rescan", "yes"]
            result = subprocess.run(cmd, capture_output=True, text=True) # Don't check=True yet
            
            if result.returncode != 0:
                logger.error(f"Wifi Scan Error: {result.stderr}")
                return []
            
            networks = []
            seen_ssids = set()
            
            for line in result.stdout.strip().split('\n'):
                parts = line.split(':')
                if len(parts) >= 2:
                    ssid = parts[0]
                    if not ssid or ssid in seen_ssids:
                        continue
                    try:
                        signal = int(parts[1])
                    except:
                        signal = 0
                    security = parts[2] if len(parts) > 2 else ""
                    networks.append({"ssid": ssid, "signal": signal, "security": security})
                    seen_ssids.add(ssid)
                    
            return sorted(networks, key=lambda x: x['signal'], reverse=True)
            
        except Exception as e:
            logger.error(f"Wifi Scan Failed: {e}")
            return []

    def connect_network(self, ssid: str, password: str) -> bool:
        if self.mock_mode:
            logger.info(f"Mock Connecting to {ssid}...")
            return True
            
        try:
            # 1. Cleanup existing connection profile for this SSID (avoids conflict/stale secrets)
            # failure here is fine (e.g. doesn't exist)
            subprocess.run([self.nmcli_path, "connection", "delete", ssid], capture_output=True)

            # 2. Connect
            # nmcli dev wifi connect <ssid> password <password>
            cmd = [self.nmcli_path, "dev", "wifi", "connect", ssid, "password", password]
            
            # Use run with capture_output to get detailed error
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            
            # Failed
            err_msg = result.stderr or result.stdout or "Unknown Error"
            logger.error(f"Wifi Connect Failed: {err_msg}")
            
            # Write to debug log for user visibility
            try:
                import os
                home = os.path.expanduser("~")
                with open(os.path.join(home, "wifi_connect_error.log"), "w") as f:
                    f.write(f"SSID: {ssid}\nError: {err_msg}\n")
            except:
                pass
                
            return False
            
        except Exception as e:
            logger.error(f"Wifi Connect Exception: {e}")
            return False

    def get_status(self) -> Dict:
        if self.mock_mode:
            return {"connected": True, "ssid": "Mock Network 5G", "ip": "192.168.1.5"}
            
        try:
            # Check connection status
            # simple check: nmcli -t -f NAME,DEVICE connection show --active
            cmd = [self.nmcli_path, "-t", "-f", "NAME,TYPE", "connection", "show", "--active"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            active_ssid = None
            for line in result.stdout.strip().split('\n'):
                if ":802-11-wireless" in line or ":wifi" in line: # Type matches wifi
                    active_ssid = line.split(':')[0]
                    break
            
            # Get IP specifically for this active wifi connection/device
            # Try to identify the device from the active connection or just assume wlan0?
            # Safer to find the device that has the active wifi connection.
            
            # Simple approach: Find the device associated with the active wifi connection
            # But wait, we iterate active connections above.
            # let's try to get IP from the device we found. 
            
            # Better: `nmcli -t -f IP4.ADDRESS dev show wlan0` (assuming wlan0 is the mainly used one)
            # Or iterate devices.
            
            ip = "Unknown"
            try:
                # Find wifi device name first?
                # nmcli -t -f DEVICE,TYPE dev status | grep wifi
                # Let's verify standard wlan0 first.
                
                cmd_ip = [self.nmcli_path, "-t", "-f", "IP4.ADDRESS", "dev", "show", "wlan0"]
                res_ip = subprocess.run(cmd_ip, capture_output=True, text=True)
                if res_ip.returncode == 0 and res_ip.stdout.strip():
                    # Output is like "192.168.1.55/24"
                    ip = res_ip.stdout.strip().split('/')[0]
            except:
                pass

            return {
                "connected": active_ssid is not None,
                "ssid": active_ssid,
                "ip": ip
            }
            
        except Exception as e:
            logger.error(f"Wifi Status Failed: {e}")
            return {"connected": False, "error": str(e)}
