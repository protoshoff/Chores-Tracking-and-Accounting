#!/bin/bash
# Timezone diagnostic script for Raspberry Pi

echo "==================================="
echo "TIMEZONE DIAGNOSTIC"
echo "==================================="
echo ""
echo "1. System Timezone:"
timedatectl | grep "Time zone"
echo ""
echo "2. Current Date/Time (system):"
date
echo ""
echo "3. Current Date/Time (UTC):"
date -u
echo ""
echo "4. TZ Environment Variable:"
echo "TZ=${TZ:-not set}"
echo ""
echo "5. /etc/timezone contents:"
cat /etc/timezone 2>/dev/null || echo "File not found"
echo ""
echo "6. Symlink /etc/localtime:"
ls -l /etc/localtime
echo ""
echo "7. Python timezone check:"
python3 -c "from datetime import datetime; import time; print(f'datetime.now(): {datetime.now()}'); print(f'Local timezone: {time.tzname}')"
echo ""
echo "==================================="
echo "TO FIX TIMEZONE (if wrong):"
echo "sudo timedatectl set-timezone America/Denver"
echo "sudo systemctl restart chores-kiosk"
echo "==================================="
