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

    def _log_debug(self, msg):
        try:
            with open("/tmp/wifi_debug_service.log", "a") as f:
                f.write(f"{msg}\n")
        except:
            pass

    def scan_networks(self) -> List[Dict]:
        """Returns list of {ssid, signal, security}"""
        if self.mock_mode:
            return [{"ssid": "Mock Network", "signal": 100, "security": "WPA2"}]
        
        try:
            self._log_debug("--- Starting Scan ---")
            # 1. Ensure WiFi is on
            import time
            subprocess.run([self.nmcli_path, "radio", "wifi", "on"], check=False)
            time.sleep(4)
            
            # 2. Run nmcli
            cmd = [self.nmcli_path, "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list", "--rescan", "yes"]
            self._log_debug(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True) # Don't check=True yet
            
            self._log_debug(f"Return Code: {result.returncode}")
            self._log_debug(f"Stdout: {result.stdout}")
            self._log_debug(f"Stderr: {result.stderr}")
            
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
                    
            self._log_debug(f"Found {len(networks)} networks")
            return sorted(networks, key=lambda x: x['signal'], reverse=True)
            
        except Exception as e:
            self._log_debug(f"Exception: {str(e)}")
            logger.error(f"Wifi Scan Failed: {e}")
            return []

    def connect_network(self, ssid: str, password: str) -> bool:
        if self.mock_mode:
            logger.info(f"Mock Connecting to {ssid}...")
            return True
            
        try:
            # nmcli dev wifi connect <ssid> password <password>
            cmd = [self.nmcli_path, "dev", "wifi", "connect", ssid, "password", password]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Wifi Connect Failed: {e}")
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
            
            # Get IP
            ip_cmd = ["hostname", "-I"]
            ip_res = subprocess.run(ip_cmd, capture_output=True, text=True)
            ip = ip_res.stdout.strip().split(' ')[0] if ip_res.stdout else "Unknown"

            return {
                "connected": active_ssid is not None,
                "ssid": active_ssid,
                "ip": ip
            }
            
        except Exception as e:
            logger.error(f"Wifi Status Failed: {e}")
            return {"connected": False, "error": str(e)}
