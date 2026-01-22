#!/bin/bash
# scripts/disk_usage_report.sh
# Quick diagnostic to show what's eating disk space

echo "=== Disk Usage Report ==="
echo ""
echo "Overall Disk Usage:"
df -h /
echo ""
echo "Top 10 Largest Directories in /home/$USER:"
du -h --max-depth=2 /home/$USER 2>/dev/null | sort -hr | head -10
echo ""
echo "Release Directory Breakdown:"
if [ -d "/home/$USER/chores_app/releases" ]; then
    du -sh /home/$USER/chores_app/releases/*/ 2>/dev/null | sort -hr
else
    echo "  No releases directory found"
fi
echo ""
echo "Temp/Cache Directories:"
du -sh /tmp 2>/dev/null
du -sh /home/$USER/.cache 2>/dev/null
