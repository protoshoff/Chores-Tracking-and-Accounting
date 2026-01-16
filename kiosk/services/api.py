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
            resp = requests.post(f"{BASE_URL}/chores/{chore_id}/complete", json=payload)
            if resp.status_code in (200, 201):
                return True
            print(f"API Error complete_chore code: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"API Error complete_chore: {e}")
        return False
