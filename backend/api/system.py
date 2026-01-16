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
