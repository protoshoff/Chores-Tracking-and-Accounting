from fastapi import APIRouter, HTTPException, Body
from typing import List
from ..services.wifi import WifiService

router = APIRouter(prefix="/api/system", tags=["System"])
wifi_service = WifiService() # Singleton-ish

@router.get("/status")
def system_status():
    """General system health + wifi status"""
    wifi = wifi_service.get_status()
    return {
        "online": True,
        "version": "0.1.0",
        "wifi": wifi
    }

@router.get("/wifi/scan")
def scan_wifi():
    return wifi_service.scan_networks()

@router.post("/wifi/connect")
def connect_wifi(payload: dict = Body(...)):
    """Payload: {ssid: str, password: str}"""
    ssid = payload.get("ssid")
    password = payload.get("password")
    
    if not ssid:
        raise HTTPException(status_code=400, detail="SSID required")
        
    success = wifi_service.connect_network(ssid, password)
    if success:
        return {"status": "connected", "ssid": ssid}
    else:
        raise HTTPException(status_code=500, detail="Connection Failed")

# --- PIN Management ---
from ..db import get_session
from ..models import Settings
from sqlmodel import Session
from fastapi import Depends

@router.post("/pin/verify")
def verify_pin(payload: dict = Body(...), session: Session = Depends(get_session)):
    """Verify parent PIN. Payload: {pin: "..."}"""
    input_pin = payload.get("pin")
    if not input_pin:
        return {"valid": False}
        
    # Get stored PIN or default
    setting = session.get(Settings, "parent_pin")
    stored_pin = setting.value if setting else "1234"
    
    return {"valid": input_pin == stored_pin}

@router.put("/pin")
def update_pin(payload: dict = Body(...), session: Session = Depends(get_session)):
    """Update parent PIN. Payload: {pin: "..."}"""
    new_pin = payload.get("pin")
    if not new_pin or len(new_pin) < 4:
         raise HTTPException(status_code=400, detail="PIN must be at least 4 digits")
         
    setting = session.get(Settings, "parent_pin")
    if not setting:
        setting = Settings(key="parent_pin", value=new_pin)
    else:
        setting.value = new_pin
        
    session.add(setting)
    session.commit()
    return {"status": "updated"}
