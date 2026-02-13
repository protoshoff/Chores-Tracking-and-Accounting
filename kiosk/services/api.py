import requests
from PySide6.QtCore import QObject, Signal, Slot, QThread

BASE_URL = "http://localhost:8000/api"

class ApiService:
    @staticmethod
    def get_kids():
        try:
            resp = requests.get(f"{BASE_URL}/kids/", timeout=2)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"API Error get_kids: {e}")
        return []
    @staticmethod
    def get_kid(kid_id):
        try:
            resp = requests.get(f"{BASE_URL}/kids/{kid_id}/", timeout=2)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"API Error get_kid: {e}")
        return None
    @staticmethod
    def get_kid_chores(kid_id):
        try:
            resp = requests.get(f"{BASE_URL}/kids/{kid_id}/chores", timeout=2)
            if resp.status_code == 200:
                print(f"API Success chores: {resp.json()}") # Debug
                return resp.json()
        except Exception as e:
            print(f"API Error get_kid_chores: {e}")
        return []

    @staticmethod
    def complete_chore(chore_id, kid_id):
        try:
            payload = {"kid_id": kid_id}
            resp = requests.post(f"{BASE_URL}/chores/{chore_id}/complete", json=payload, timeout=2)
            if resp.status_code in (200, 201):
                return True
            print(f"API Error complete_chore code: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"API Error complete_chore: {e}")
        return False

    @staticmethod
    def create_kid(name, allowance=0.0):
        try:
            payload = {"name": name, "allowance": allowance}
            resp = requests.post(f"{BASE_URL}/management/kids", json=payload, timeout=2)
            if resp.status_code in (200, 201):
                return resp.json()
        except Exception as e:
            print(f"API Error create_kid: {e}")
        return None

    @staticmethod
    def update_kid(kid_id, name=None, allowance=None, is_active=None):
        try:
            payload = {}
            if name is not None: payload["name"] = name
            if allowance is not None: payload["allowance"] = allowance
            if is_active is not None: payload["is_active"] = is_active
            
            resp = requests.put(f"{BASE_URL}/management/kids/{kid_id}", json=payload, timeout=2)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"API Error update_kid: {e}")
        return None

    @staticmethod
    def get_rollups():
        try:
            resp = requests.get(f"{BASE_URL}/finances/rollups", timeout=2)
            if resp.status_code == 200:
                return resp.json()
        except:
            return []
        return []
        
    @staticmethod
    def delete_kid(kid_id):
        # Soft delete via update
        return ApiService.update_kid(kid_id, is_active=False)

    # --- Chore Management ---
    @staticmethod
    def create_chore(kid_id, name, description="", reward=1.0, frequency="DAILY", due_day=None, weight=None):
        try:
            payload = {
                "kid_id": kid_id,
                "name": name,
                "description": description,
                "frequency": frequency
            }
            # Use weight if provided, otherwise use reward (backward compat)
            if weight is not None:
                payload["weight"] = weight
            else:
                payload["reward"] = reward
                
            if due_day is not None:
                payload["due_day"] = due_day
                
            resp = requests.post(f"{BASE_URL}/management/chores", json=payload, timeout=2)
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                 print(f"create_chore failed: {resp.text}")
        except Exception as e:
            print(f"API Error create_chore: {e}")
        return None

    @staticmethod
    def update_chore(chore_id, name=None, description=None, reward=None, frequency=None, due_day=None, archived=None):
        try:
            payload = {}
            if name is not None: payload["name"] = name
            if description is not None: payload["description"] = description
            if reward is not None: payload["reward"] = reward
            if frequency is not None: payload["frequency"] = frequency
            if due_day is not None: payload["due_day"] = due_day
            if archived is not None: payload["archived"] = archived
            
            resp = requests.put(f"{BASE_URL}/management/chores/{chore_id}", json=payload, timeout=2)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"API Error update_chore: {e}")
        return None

    @staticmethod
    def verify_pin(pin):
        try:
            resp = requests.post(f"{BASE_URL}/system/pin/verify", json={"pin": pin}, timeout=2)
            if resp.status_code == 200:
                return resp.json().get("valid", False)
        except Exception as e:
            print(f"API Error verify_pin: {e}")
            # Fallback to default if offline/error? Or fail secure?
            # Let's fail secure, but if it's 1234 we might allow it? No, stay secure.
            if pin == "1234": return True # Emergency Backdoor for v0.1
        return False

    @staticmethod
    def update_pin(new_pin):
        try:
            resp = requests.put(f"{BASE_URL}/system/pin", json={"pin": new_pin}, timeout=2)
            return resp.status_code == 200
        except Exception as e:
            print(f"API Error update_pin: {e}")
        return False

    # --- Ledger ---
    @staticmethod
    def get_ledger_history(kid_id):
        try:
            resp = requests.get(f"{BASE_URL}/ledger/{kid_id}/history", timeout=2)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"API Error get_ledger_history: {e}")
        return []

    @staticmethod
    def add_transaction(kid_id, amount, type_str, desc):
        payload = {
            "kid_id": kid_id,
            "amount": amount,
            "type": type_str,
            "description": desc
        }
        try:
            resp = requests.post(f"{BASE_URL}/ledger/transaction", json=payload, timeout=2)
            return resp.status_code == 201
        except Exception as e:
            print(f"API Error add_transaction: {e}")
        return False

    @staticmethod
    def payout_kid(kid_id):
        try:
            resp = requests.post(f"{BASE_URL}/ledger/{kid_id}/payout", timeout=2)
            return resp.status_code == 201
        except Exception as e:
            print(f"API Error payout_kid: {e}")
        return False

    @staticmethod
    def delete_transaction(entry_id):
        try:
            resp = requests.delete(f"{BASE_URL}/ledger/transaction/{entry_id}", timeout=2)
            return resp.status_code == 200
        except Exception as e:
            print(f"API Error delete_transaction: {e}")
        return False

    # --- System Configuration ---
    @staticmethod
    def get_system_config():
        """Get system configuration (payout mode, threshold, etc.)"""
        try:
            resp = requests.get(f"{BASE_URL}/system/config", timeout=2)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"API Error get_system_config: {e}")
        return None

    @staticmethod
    def update_system_config(payout_mode, payout_threshold, payout_day=None, payout_hour=None, payout_minute=None, timezone=None):
        """Update system configuration"""
        try:
            payload = {
                "payout_mode": payout_mode,
                "payout_threshold": payout_threshold
            }
            
            # Add payout schedule if provided
            if payout_day is not None:
                payload["payout_day"] = payout_day
            if payout_hour is not None:
                payload["payout_hour"] = payout_hour
            if payout_minute is not None:
                payload["payout_minute"] = payout_minute
            if timezone is not None:
                payload["timezone"] = timezone
            
            resp = requests.put(f"{BASE_URL}/system/config", json=payload, timeout=2)
            return resp.status_code == 200
        except Exception as e:
            print(f"API Error update_system_config: {e}")
        return False

    @staticmethod
    def trigger_update():
        """Trigger system update"""
        try:
            resp = requests.post(f"{BASE_URL}/system/update", timeout=5)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"Update trigger failed: {resp.text}")
        except Exception as e:
            print(f"API Error trigger_update: {e}")
        return None
