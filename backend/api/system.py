from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session
from ..db import get_session
from ..models import Settings
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

class WifiConnectRequest(BaseModel):
    ssid: str
    password: Optional[str] = None

class PinRequest(BaseModel):
    pin: str

class ConfigUpdate(BaseModel):
    payout_mode: Optional[str] = None
    payout_threshold: Optional[int] = None
    payout_day: Optional[int] = None
    payout_hour: Optional[int] = None
    payout_minute: Optional[int] = None
    timezone: Optional[str] = None

@router.post("/wifi/connect")
def connect_wifi(payload: WifiConnectRequest):
    ssid = payload.ssid
    password = payload.password
        
    success = wifi_service.connect_network(ssid, password)
    if success:
        return {"status": "connected", "ssid": ssid}
    else:
        raise HTTPException(status_code=500, detail="Connection Failed")

# --- PIN Management ---

@router.post("/pin/verify")
def verify_pin_endpoint(payload: PinRequest, session: Session = Depends(get_session)):
    """Verify parent PIN."""
    from ..services.pin import verify_pin, hash_pin
    
    input_pin = payload.pin
    if not input_pin:
        return {"valid": False}
        
    # Get stored PIN or default
    setting = session.get(Settings, "parent_pin")
    stored_pin = setting.value if setting else "1234"
    
    valid = verify_pin(input_pin, stored_pin)
    
    # Auto-migrate plaintext PIN to bcrypt on successful verify
    if valid and not stored_pin.startswith("$2"):
        if not setting:
            setting = Settings(key="parent_pin", value=hash_pin(input_pin))
        else:
            setting.value = hash_pin(input_pin)
        session.add(setting)
        session.commit()
    
    return {"valid": valid}

@router.put("/pin")
def update_pin(payload: PinRequest, session: Session = Depends(get_session)):
    """Update parent PIN."""
    from ..services.pin import hash_pin
    
    new_pin = payload.pin
    if not new_pin or len(new_pin) < 4:
         raise HTTPException(status_code=400, detail="PIN must be at least 4 digits")
         
    hashed = hash_pin(new_pin)
    setting = session.get(Settings, "parent_pin")
    if not setting:
        setting = Settings(key="parent_pin", value=hashed)
    else:
        setting.value = hashed
        
    session.add(setting)
    session.commit()
    return {"status": "updated"}

# --- General Config ---
@router.get("/config")
def get_config(session: Session = Depends(get_session)):
    """Get system config (payout_mode, payout_threshold, timezone, etc)."""
    # Defaults
    config = {
        "payout_mode": "ALL_OR_NOTHING",
        "payout_threshold": 80,
        "timezone": "America/Phoenix"
    }
    
    # Load overrides
    mode_setting = session.get(Settings, "payout_mode")
    if mode_setting:
        config["payout_mode"] = mode_setting.value
    
    threshold_setting = session.get(Settings, "payout_threshold")
    if threshold_setting:
        try:
            config["payout_threshold"] = int(threshold_setting.value)
        except Exception:
            pass
    
    # Load timezone
    tz_setting = session.get(Settings, "timezone")
    if tz_setting:
        config["timezone"] = tz_setting.value
    
    # Load payout schedule
    day_setting = session.get(Settings, "payout_day")
    hour_setting = session.get(Settings, "payout_hour")
    minute_setting = session.get(Settings, "payout_minute")
    
    if day_setting:
        config["payout_day"] = int(day_setting.value)
    if hour_setting:
        config["payout_hour"] = int(hour_setting.value)
    if minute_setting:
        config["payout_minute"] = int(minute_setting.value)
            
    return config

def _upsert_setting(session: Session, key: str, value: str):
    """Helper to insert or update a Settings row."""
    setting = session.get(Settings, key)
    if not setting:
        setting = Settings(key=key, value=value)
    else:
        setting.value = value
    session.add(setting)

@router.put("/config")
def update_config(payload: ConfigUpdate, session: Session = Depends(get_session)):
    """Update system config."""
    if payload.payout_mode is not None:
        if payload.payout_mode not in ["PRORATED", "ALL_OR_NOTHING"]:
            raise HTTPException(status_code=400, detail="Invalid payout mode. Must be PRORATED or ALL_OR_NOTHING")
        _upsert_setting(session, "payout_mode", payload.payout_mode)

    if payload.payout_threshold is not None:
        if payload.payout_threshold < 0 or payload.payout_threshold > 100:
            raise HTTPException(status_code=400, detail="Threshold must be 0-100")
        _upsert_setting(session, "payout_threshold", str(payload.payout_threshold))

    if payload.payout_day is not None:
        if payload.payout_day < 0 or payload.payout_day > 6:
            raise HTTPException(status_code=400, detail="Payout day must be 0-6")
        _upsert_setting(session, "payout_day", str(payload.payout_day))

    if payload.payout_hour is not None:
        if payload.payout_hour < 0 or payload.payout_hour > 23:
            raise HTTPException(status_code=400, detail="Payout hour must be 0-23")
        _upsert_setting(session, "payout_hour", str(payload.payout_hour))

    if payload.payout_minute is not None:
        if payload.payout_minute < 0 or payload.payout_minute > 59:
            raise HTTPException(status_code=400, detail="Payout minute must be 0-59")
        _upsert_setting(session, "payout_minute", str(payload.payout_minute))

    if payload.timezone is not None:
        if not payload.timezone:
            raise HTTPException(status_code=400, detail="Timezone must be a valid string")
        _upsert_setting(session, "timezone", payload.timezone)

    session.commit()

    # If timezone changed, trigger automation restart
    if payload.timezone is not None:
        try:
            from ..services.automation import get_automation_service
            automation = get_automation_service()
            if automation:
                automation.schedule_weekly_tally()
        except Exception:
            pass

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
    # Check if chores_repo deployment directory exists in user's home
    home_dir = os.path.expanduser("~")
    if not os.path.exists(f"{home_dir}/chores_repo"):
        raise HTTPException(status_code=403, detail="Updates only allowed on Pi")
    
    try:
        # Get home directory of running user (supports any username)
        script_path = f"{home_dir}/chores_repo/scripts/deploy_release.sh"
        
        # Run deploy script in background (detached from parent process)
        log_path = os.path.join(home_dir, "chores_app", "deploy.log")
        log_file = open(log_path, "a")
        subprocess.Popen(
            [script_path],
            stdout=log_file,
            stderr=log_file,
            start_new_session=True
        )
        return {"status": "update_started", "message": "System update initiated. Kiosk will restart in ~60 seconds."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
