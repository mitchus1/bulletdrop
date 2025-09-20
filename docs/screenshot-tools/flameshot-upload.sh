#!/bin/bash
# BulletDrop upload script for Flameshot (Linux)
# Place this script in ~/.local/bin/ and make it executable
# Add a keyboard shortcut to run this script

# Configuration - UPDATE THESE VALUES
JWT_TOKEN="your_jwt_token_here"
SERVER_URL="http://localhost:8000/api/uploads/sharex"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check dependencies
check_dependencies() {
    local missing_deps=()

    command -v flameshot >/dev/null 2>&1 || missing_deps+=("flameshot")
    command -v curl >/dev/null 2>&1 || missing_deps+=("curl")
    command -v jq >/dev/null 2>&1 || missing_deps+=("jq")
    command -v xclip >/dev/null 2>&1 || missing_deps+=("xclip")

    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}Missing dependencies: ${missing_deps[*]}${NC}"
        echo "Install with:"
        echo "  Ubuntu/Debian: sudo apt install ${missing_deps[*]}"
        echo "  Arch Linux: sudo pacman -S ${missing_deps[*]}"
        echo "  Fedora: sudo dnf install ${missing_deps[*]}"
        exit 1
    fi
}

# Check if JWT token is configured
check_config() {
    if [ "$JWT_TOKEN" = "your_jwt_token_here" ]; then
        echo -e "${YELLOW}Please configure your JWT token in this script${NC}"
        echo "1. Login to BulletDrop"
        echo "2. Open browser dev tools (F12)"
        echo "3. Go to Application > Local Storage"
        echo "4. Copy the 'token' value and replace JWT_TOKEN in this script"
        exit 1
    fi
}

# Send notification
notify() {
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "BulletDrop" "$1"
    fi
}

# Main upload function
upload_screenshot() {
    echo -e "${YELLOW}Taking screenshot...${NC}"

    # Create temporary file
    TEMP_FILE=$(mktemp --suffix=.png)

    # Take screenshot with Flameshot
    flameshot gui --raw > "$TEMP_FILE" 2>/dev/null

    # Check if screenshot was taken (file exists and has content)
    if [ ! -s "$TEMP_FILE" ]; then
        echo -e "${YELLOW}No screenshot taken or cancelled${NC}"
        rm -f "$TEMP_FILE"
        exit 0
    fi

    echo -e "${YELLOW}Uploading to BulletDrop...${NC}"

    # Upload to BulletDrop
    RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "User-Agent: BulletDrop-Flameshot/1.0" \
        -F "file=@$TEMP_FILE" \
        "$SERVER_URL" 2>/dev/null)

    # Check if curl succeeded
    if [ $? -ne 0 ]; then
        echo -e "${RED}Upload failed: Network error${NC}"
        notify "Upload failed: Network error"
        rm -f "$TEMP_FILE"
        exit 1
    fi

    # Parse response
    URL=$(echo "$RESPONSE" | jq -r '.url' 2>/dev/null)
    ERROR=$(echo "$RESPONSE" | jq -r '.detail' 2>/dev/null)

    if [ "$URL" != "null" ] && [ -n "$URL" ]; then
        # Success - copy URL to clipboard
        echo "$URL" | xclip -selection clipboard
        echo -e "${GREEN}✓ Screenshot uploaded successfully!${NC}"
        echo -e "${GREEN}URL: $URL${NC}"
        echo -e "${GREEN}URL copied to clipboard${NC}"
        notify "Screenshot uploaded! URL copied to clipboard."
    else
        # Failed - show error
        if [ "$ERROR" != "null" ] && [ -n "$ERROR" ]; then
            echo -e "${RED}Upload failed: $ERROR${NC}"
            notify "Upload failed: $ERROR"
        else
            echo -e "${RED}Upload failed: Unknown error${NC}"
            echo -e "${RED}Response: $RESPONSE${NC}"
            notify "Upload failed: Unknown error"
        fi
        rm -f "$TEMP_FILE"
        exit 1
    fi

    # Cleanup
    rm -f "$TEMP_FILE"
}

# Main execution
main() {
    echo -e "${GREEN}BulletDrop Screenshot Uploader${NC}"

    check_dependencies
    check_config
    upload_screenshot
}

# Run main function
main "$@"