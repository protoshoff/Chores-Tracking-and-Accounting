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

# --- General Config ---
@router.get("/config")
def get_config(session: Session = Depends(get_session)):
    """Get system config (payout_mode, payout_threshold, etc)."""
    # Defaults
    config = {
        "payout_mode": "ALL_OR_NOTHING",
        "payout_threshold": 80
    }
    
    # Load overrides
    mode_setting = session.get(Settings, "payout_mode")
    if mode_setting:
        config["payout_mode"] = mode_setting.value
    
    threshold_setting = session.get(Settings, "payout_threshold")
    if threshold_setting:
        try:
            config["payout_threshold"] = int(threshold_setting.value)
        except:
            pass
            
    return config

@router.put("/config")
def update_config(payload: dict = Body(...), session: Session = Depends(get_session)):
    """Update system config."""
    # Payout Mode
    if "payout_mode" in payload:
        mode = payload["payout_mode"]
        if mode not in ["PRORATED", "ALL_OR_NOTHING"]:
            raise HTTPException(status_code=400, detail="Invalid payout mode. Must be PRORATED or ALL_OR_NOTHING")
        
        setting = session.get(Settings, "payout_mode")
        if not setting:
            setting = Settings(key="payout_mode", value=mode)
        else:
            setting.value = mode
        session.add(setting)
    
    # Payout Threshold
    if "payout_threshold" in payload:
        val = payload["payout_threshold"]
        try:
            val_int = int(val)
            if val_int < 0 or val_int > 100:
                raise ValueError
            
            setting = session.get(Settings, "payout_threshold")
            if not setting:
                setting = Settings(key="payout_threshold", value=str(val_int))
            else:
                setting.value = str(val_int)
            session.add(setting)
        except ValueError:
            raise HTTPException(status_code=400, detail="Threshold must be 0-100")
            
    session.commit()
    return {"status": "success"}

@router.post("/update")
async def trigger_system_update():
    """
    Trigger system update by running deploy_release.sh script.
    Runs in background to avoid blocking. Pi-only for safety.
    """
    import subprocess
    import os
    
    # Security: Only allow on Pi, not dev machines
    if not os.path.exists("/home/chores"):
        raise HTTPException(status_code=403, detail="Updates only allowed on Pi")
    
    try:
        # Run deploy script in background (detached from parent process)
        subprocess.Popen(
            ["/home/chores/chores_app/current/scripts/deploy_release.sh"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return {"status": "update_started", "message": "System update initiated. Kiosk will restart in ~60 seconds."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
