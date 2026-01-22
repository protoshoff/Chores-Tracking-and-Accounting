#!/bin/bash
# scripts/cleanup_old_releases.sh
# Removes old release directories, keeping only the current and 1 previous (for rollback)

set -e

APP_ROOT="/home/$USER/chores_app"
RELEASES_DIR="$APP_ROOT/releases"
CURRENT_LINK="$APP_ROOT/current"

echo "=== Chores App - Release Cleanup ==="

# Check if releases directory exists
if [ ! -d "$RELEASES_DIR" ]; then
    echo "No releases directory found at $RELEASES_DIR"
    exit 0
fi

# Get the current release (what the symlink points to)
if [ -L "$CURRENT_LINK" ]; then
    CURRENT_RELEASE=$(readlink -f "$CURRENT_LINK")
    CURRENT_BASENAME=$(basename "$CURRENT_RELEASE")
    echo "Current release: $CURRENT_BASENAME"
else
    echo "Warning: No 'current' symlink found"
    CURRENT_RELEASE=""
    CURRENT_BASENAME=""
fi

# List all releases sorted by modification time (newest first)
cd "$RELEASES_DIR"
RELEASES=($(ls -dt */))

echo "Found ${#RELEASES[@]} release(s)"

# Keep current + 1 previous (for rollback capability)
KEEP_COUNT=2
DELETED_COUNT=0
FREED_SPACE=0

for ((i=0; i<${#RELEASES[@]}; i++)); do
    RELEASE_DIR="${RELEASES[$i]%/}"  # Remove trailing slash
    FULL_PATH="$RELEASES_DIR/$RELEASE_DIR"
    
    # Skip if this is the current release
    if [ "$FULL_PATH" = "$CURRENT_RELEASE" ]; then
        echo "  [KEEP] $RELEASE_DIR (current)"
        continue
    fi
    
    # Keep the first N-1 non-current releases (for rollback)
    if [ $i -lt $KEEP_COUNT ]; then
        echo "  [KEEP] $RELEASE_DIR (rollback candidate)"
        continue
    fi
    
    # Delete this old release
    echo "  [DELETE] $RELEASE_DIR"
    
    # Calculate size before deletion
    SIZE=$(du -sm "$FULL_PATH" 2>/dev/null | cut -f1)
    
    rm -rf "$FULL_PATH"
    DELETED_COUNT=$((DELETED_COUNT + 1))
    FREED_SPACE=$((FREED_SPACE + SIZE))
done

echo ""
echo "=== Cleanup Summary ==="
echo "Deleted: $DELETED_COUNT old release(s)"
echo "Freed: ~${FREED_SPACE}MB"
echo ""
echo "Remaining releases:"
ls -lh "$RELEASES_DIR"
