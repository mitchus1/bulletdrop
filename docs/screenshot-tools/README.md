# Screenshot Tool Integration with BulletDrop

BulletDrop supports automatic screenshot uploading through various screenshot tools. This guide covers setup for different platforms.

## Quick Setup

1. **Get your JWT token**: Login to BulletDrop and copy your JWT token from browser dev tools
2. **Choose your tool**: Windows (ShareX), Linux (Flameshot), macOS (custom script)
3. **Configure upload endpoint**: Use the `/api/uploads/sharex` endpoint for compatibility

## ShareX (Windows)

ShareX is the most popular screenshot tool for Windows with excellent custom uploader support.

### Installation
1. Download ShareX from [getsharex.com](https://getsharex.com/)
2. Install and run ShareX

### Configuration
1. In ShareX, go to **Destinations** > **Custom uploader settings**
2. Click **Import** > **From file**
3. Select the `sharex-config.sxcu` file from this directory
4. **IMPORTANT**: Replace `YOUR_JWT_TOKEN_HERE` with your actual JWT token:
   - Click **Edit** on the BulletDrop uploader
   - In Headers section, update the Authorization value to: `Bearer your_actual_jwt_token`
5. Set BulletDrop as your default image destination:
   - Go to **Destinations** > **Image uploader** > **Custom image uploader** > **BulletDrop**

### Getting Your JWT Token
1. Login to BulletDrop web interface
2. Open browser developer tools (F12)
3. Go to **Application** > **Local Storage** > **http://localhost:3000**
4. Copy the value of the `token` key

### Usage
- Take screenshots with **Print Screen** or **Ctrl+Shift+4**
- Files are automatically uploaded to your BulletDrop account
- URLs are copied to clipboard for easy sharing

## Flameshot (Linux)

Flameshot is a powerful screenshot tool for Linux that can be configured to upload to custom servers.

### Installation
```bash
# Ubuntu/Debian
sudo apt install flameshot

# Arch Linux
sudo pacman -S flameshot

# Fedora
sudo dnf install flameshot
```

### Configuration Script
Create an upload script at `~/.local/bin/bulletdrop-upload`:

```bash
#!/bin/bash
# BulletDrop upload script for Flameshot

# Your BulletDrop JWT token
JWT_TOKEN="your_jwt_token_here"

# Server URL
SERVER_URL="http://localhost:8000/api/uploads/sharex"

# Take screenshot and save to temp file
TEMP_FILE=$(mktemp --suffix=.png)
flameshot gui --raw > "$TEMP_FILE"

# Check if screenshot was taken
if [ -s "$TEMP_FILE" ]; then
    # Upload to BulletDrop
    RESPONSE=$(curl -s -X POST \\
        -H "Authorization: Bearer $JWT_TOKEN" \\
        -F "file=@$TEMP_FILE" \\
        "$SERVER_URL")

    # Extract URL from response
    URL=$(echo "$RESPONSE" | jq -r '.url')

    if [ "$URL" != "null" ]; then
        # Copy URL to clipboard
        echo "$URL" | xclip -selection clipboard
        notify-send "BulletDrop" "Screenshot uploaded! URL copied to clipboard."
        echo "Uploaded: $URL"
    else
        notify-send "BulletDrop" "Upload failed!"
        echo "Upload failed: $RESPONSE"
    fi
else
    echo "No screenshot taken"
fi

# Cleanup
rm -f "$TEMP_FILE"
```

Make it executable:
```bash
chmod +x ~/.local/bin/bulletdrop-upload
```

### Dependencies
```bash
# Install required tools
sudo apt install jq xclip  # Ubuntu/Debian
sudo pacman -S jq xclip    # Arch Linux
sudo dnf install jq xclip  # Fedora
```

### Keyboard Shortcut
Add a keyboard shortcut in your desktop environment:
- Command: `~/.local/bin/bulletdrop-upload`
- Shortcut: `Ctrl+Shift+S` (or your preference)

## macOS (Custom Script)

For macOS, you can use a custom script with the built-in `screencapture` command.

### Script Setup
Create a script at `~/bin/bulletdrop-screenshot`:

```bash
#!/bin/bash
# BulletDrop screenshot script for macOS

JWT_TOKEN="your_jwt_token_here"
SERVER_URL="http://localhost:8000/api/uploads/sharex"

# Take screenshot
TEMP_FILE=$(mktemp).png
screencapture -i "$TEMP_FILE"

if [ -f "$TEMP_FILE" ] && [ -s "$TEMP_FILE" ]; then
    # Upload to BulletDrop
    RESPONSE=$(curl -s -X POST \\
        -H "Authorization: Bearer $JWT_TOKEN" \\
        -F "file=@$TEMP_FILE" \\
        "$SERVER_URL")

    URL=$(echo "$RESPONSE" | jq -r '.url')

    if [ "$URL" != "null" ]; then
        echo "$URL" | pbcopy
        osascript -e 'display notification "Screenshot uploaded! URL copied to clipboard." with title "BulletDrop"'
        echo "Uploaded: $URL"
    else
        osascript -e 'display notification "Upload failed!" with title "BulletDrop"'
        echo "Upload failed: $RESPONSE"
    fi
fi

rm -f "$TEMP_FILE"
```

Make executable and add to PATH:
```bash
chmod +x ~/bin/bulletdrop-screenshot
```

## API Endpoints

### Upload Endpoint
- **URL**: `POST /api/uploads/sharex`
- **Authentication**: Bearer JWT token
- **Content-Type**: `multipart/form-data`
- **File field**: `file`

### Response Format
```json
{
  "url": "https://img.bulletdrop.com/uploads/abc123.png",
  "thumbnail_url": "https://img.bulletdrop.com/uploads/abc123.png",
  "deletion_url": "http://localhost:8000/api/uploads/123/delete"
}
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check your JWT token is correct and not expired
   - Login again to get a fresh token

2. **413 File Too Large**
   - Check file size limits in your BulletDrop account
   - Compress images before uploading

3. **400 Bad Request**
   - Verify file type is supported
   - Check the upload endpoint URL

### Testing Upload
Test your configuration with curl:

```bash
curl -X POST \\
  -H "Authorization: Bearer your_jwt_token" \\
  -F "file=@test-image.png" \\
  "http://localhost:8000/api/uploads/sharex"
```

## Support

For support and issues:
- Check the BulletDrop documentation
- Verify your JWT token is valid
- Test the API endpoint directly with curl
- Check server logs for error details

## Security Notes

- Keep your JWT token secure and private
- Use HTTPS in production (update URLs accordingly)
- Tokens expire periodically - you may need to update them
- Consider using environment variables for tokens in scripts