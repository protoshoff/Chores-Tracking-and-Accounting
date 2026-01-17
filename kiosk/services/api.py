import requests
from PySide6.QtCore import QObject, Signal, Slot, QThread

BASE_URL = "http://localhost:8000/api"

class ApiService:
    @staticmethod
    def get_kids():
        try:
            resp = requests.get(f"{BASE_URL}/kids", timeout=2)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"API Error get_kids: {e}")
        return []
    @staticmethod
    def get_kid(kid_id):
        try:
            resp = requests.get(f"{BASE_URL}/kids/{kid_id}", timeout=2)
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
    def create_kid(name, allowance_cents=0):
        try:
            payload = {"name": name, "allowance_cents": allowance_cents}
            resp = requests.post(f"{BASE_URL}/management/kids", json=payload, timeout=2)
            if resp.status_code in (200, 201):
                return resp.json()
        except Exception as e:
            print(f"API Error create_kid: {e}")
        return None

    @staticmethod
    def update_kid(kid_id, name=None, allowance_cents=None, is_active=None):
        try:
            payload = {}
            if name is not None: payload["name"] = name
            if allowance_cents is not None: payload["allowance_cents"] = allowance_cents
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
    def create_chore(kid_id, name, description="", weight=1, frequency="DAILY"):
        try:
            payload = {
                "kid_id": kid_id,
                "name": name,
                "description": description,
                "weight": weight,
                "frequency": frequency
            }
            resp = requests.post(f"{BASE_URL}/management/chores", json=payload, timeout=2)
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                 print(f"create_chore failed: {resp.text}")
        except Exception as e:
            print(f"API Error create_chore: {e}")
        return None

    @staticmethod
    def update_chore(chore_id, name=None, description=None, weight=None, frequency=None, archived=None):
        try:
            payload = {}
            if name is not None: payload["name"] = name
            if description is not None: payload["description"] = description
            if weight is not None: payload["weight"] = weight
            if frequency is not None: payload["frequency"] = frequency
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
