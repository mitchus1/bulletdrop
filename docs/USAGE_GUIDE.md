# 🎯 BulletDrop Complete Usage Guide

This guide covers everything you need to know about using BulletDrop - from setup to taking screenshots and managing your files.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Frontend Web Interface](#frontend-web-interface)
3. [Screenshot Tools Setup](#screenshot-tools-setup)
4. [How to Get File Links](#how-to-get-file-links)
5. [Managing Uploads](#managing-uploads)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Step 1: Start the Application

```bash
# Terminal 1: Start Backend
cd backend
../.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend
cd frontend
npm run dev
```

### Step 2: Access the Application
- **Frontend**: http://localhost:3000 (or http://localhost:5173 with Vite)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Step 3: Create Account
1. Go to http://localhost:3000
2. Click "Create Account" or navigate to `/register`
3. Fill in username, email, and password
4. You'll be automatically logged in after registration

---

## 💻 Frontend Web Interface

### Authentication

#### Registration
- Navigate to `/register` or click "Create Account"
- Fill in:
  - **Username**: Unique identifier (used for API authentication)
  - **Email**: Valid email address
  - **Password**: Minimum 6 characters
  - **Confirm Password**: Must match password
- After successful registration, you're automatically logged in

#### Login
- Navigate to `/login` or click "Sign In"
- Enter your username and password
- You'll be redirected to the dashboard after successful login

### Dashboard Overview

The dashboard (`/dashboard`) is your main control center:

#### User Statistics Cards
- **Total Uploads**: Number of files you've uploaded
- **Storage Used**: How much storage you're using vs. your limit
- **Account Status**: Verification status (Verified/Unverified)

#### Quick Actions
- **Upload File**: Opens the drag-and-drop upload widget
- **View All Uploads**: Takes you to the full uploads page

#### Recent Uploads
- Shows your 5 most recent uploads
- Quick actions: Copy URL, View file
- Click "View all →" to see complete upload history

### File Upload Interface

#### Web Upload (Dashboard/Uploads Page)

**Drag and Drop:**
1. Drag files directly onto the upload area
2. Files are automatically validated and uploaded
3. Progress bars show upload status
4. URLs are automatically copied to clipboard on success

**Click to Upload:**
1. Click "Select files" button
2. Choose files from your computer
3. Multiple files can be selected at once

**Domain Selection:**
- Choose which domain to upload to (if you have claimed domains)
- Default uploads to the main server

#### Supported File Types
- **Images**: PNG, JPG, JPEG, GIF, WebP
- **Documents**: PDF, TXT, MD
- **Videos**: MP4, WebM (if configured)
- **Maximum Size**: 10MB per file (configurable)

### Uploads Management (`/uploads`)

#### Upload History Table
- **File Preview**: Thumbnail for images, icon for documents
- **File Info**: Original filename and MIME type
- **Size**: Human-readable file size
- **Views**: Number of times the file has been accessed
- **Upload Date**: When the file was uploaded

#### File Actions
- **Copy URL**: Copies the public URL to clipboard
- **View**: Opens the file in a new tab
- **Delete**: Permanently removes the file (with confirmation)

#### Pagination
- 20 uploads per page
- "Load More" button for additional pages
- Uploads are sorted by newest first

---

## 📸 Screenshot Tools Setup

### Windows - ShareX (Recommended)

#### Installation
1. Download ShareX from [getsharex.com](https://getsharex.com/)
2. Install and run ShareX

#### Configuration
1. In ShareX, go to **Destinations** > **Custom uploader settings**
2. Click **Import** > **From file**
3. Select `docs/screenshot-tools/sharex-config.sxcu`
4. **IMPORTANT**: Edit the imported config:
   - Click **Edit** on the BulletDrop uploader
   - Replace `YOUR_JWT_TOKEN_HERE` with your actual JWT token

#### Getting Your JWT Token
1. Login to BulletDrop web interface
2. Open browser developer tools (F12)
3. Go to **Application** > **Local Storage** > **http://localhost:3000**
4. Copy the value of the `token` key
5. Paste this into ShareX config (including "Bearer " prefix)

#### Set as Default
1. Go to **Destinations** > **Image uploader**
2. Select **Custom image uploader** > **BulletDrop**

#### Usage
- Take screenshots with **Print Screen** or **Ctrl+Shift+4**
- Files automatically upload to your BulletDrop account
- URLs are copied to clipboard for instant sharing
- ShareX shows upload progress and completion notifications

### Linux - Flameshot

#### Installation
```bash
# Ubuntu/Debian
sudo apt install flameshot jq xclip

# Arch Linux
sudo pacman -S flameshot jq xclip

# Fedora
sudo dnf install flameshot jq xclip
```

#### Setup Script
1. Copy `docs/screenshot-tools/flameshot-upload.sh` to `~/.local/bin/bulletdrop-upload`
2. Make it executable: `chmod +x ~/.local/bin/bulletdrop-upload`
3. Edit the script and replace `your_jwt_token_here` with your actual JWT token

#### Keyboard Shortcut
Add a keyboard shortcut in your desktop environment:
- **Command**: `~/.local/bin/bulletdrop-upload`
- **Shortcut**: `Ctrl+Shift+S` (or your preference)

#### Usage
1. Press your keyboard shortcut
2. Take screenshot with Flameshot selection tool
3. File automatically uploads to BulletDrop
4. URL is copied to clipboard
5. Desktop notification confirms success

### macOS - Custom Script

#### Setup
1. Create script at `~/bin/bulletdrop-screenshot`
2. Replace JWT token in the script
3. Make executable: `chmod +x ~/bin/bulletdrop-screenshot`
4. Add to PATH or create keyboard shortcut

#### Usage
- Run script manually or via keyboard shortcut
- Uses built-in `screencapture` command
- URL copied to clipboard on success

---

## 🔗 How to Get File Links

### After Upload (Multiple Ways)

#### 1. Automatic Clipboard Copy
- **Web Upload**: URL automatically copied to clipboard on successful upload
- **ShareX**: URL copied to clipboard after screenshot
- **Flameshot**: URL copied to clipboard after screenshot

#### 2. From Upload Notifications
- Green success message shows "URL copied to clipboard!"
- Click the file name in the upload progress widget

#### 3. From Dashboard
- Recent uploads section shows quick "Copy URL" buttons
- Click any "Copy URL" button to copy to clipboard

#### 4. From Uploads Page
- Full table view with "Copy URL" action for each file
- URLs are in format: `http://localhost:8000/static/category/filename.ext`

#### 5. Direct API Response
When using ShareX or API directly, the response includes:
```json
{
  "url": "http://localhost:8000/static/images/uuid-filename.png",
  "thumbnail_url": "http://localhost:8000/static/images/uuid-filename.png",
  "deletion_url": "http://localhost:8000/api/uploads/123/delete"
}
```

### Sharing Links

#### Public Access
- All uploaded files are publicly accessible by default
- No authentication needed to view files
- URLs can be shared anywhere

#### Custom Domains
- If you have claimed custom domains, files use those URLs
- Example: `https://img.bulletdrop.com/static/images/file.png`

#### URL Structure
```
http://localhost:8000/static/{category}/{uuid-filename}.{ext}

Where:
- category: images, documents, or other
- uuid: Unique identifier (prevents conflicts)
- filename: Original filename with UUID prefix
- ext: Original file extension
```

---

## 📁 Managing Uploads

### View All Uploads
1. Go to `/uploads` or click "View All Uploads" from dashboard
2. See complete table with file details
3. Search, sort, and paginate through uploads

### File Actions

#### Copy URL
- Click "Copy URL" next to any file
- URL is copied to clipboard
- Share the URL anywhere for public access

#### View File
- Click "View" to open file in new tab
- Direct access to the file
- Increment view counter for analytics

#### Delete Files
- Click "Delete" next to any file
- Confirmation dialog prevents accidental deletion
- File is permanently removed from server
- Storage quota is updated immediately

#### Update Metadata
- Custom names for uploads
- Public/private visibility settings
- Domain selection for uploads

### Storage Management

#### Quota Tracking
- Dashboard shows current usage vs. limit
- Visual progress bar with percentage
- Default limit: 1GB per user

#### Storage Tips
- Delete unused files to free up space
- Use image compression before upload
- Monitor usage on dashboard

---

## 🎛️ Advanced Features

### Domain Management

#### Available Domains
- Default domains provided by the platform
- Premium domains for advanced users
- Custom domain support (admin feature)

#### Claiming Domains
1. Go to domain management (API endpoint)
2. Claim available domains for your account
3. Set primary domain for new uploads
4. Different domains may have different file size limits

#### Domain Examples
- `img.bulletdrop.com` - Image hosting (10MB limit)
- `shots.bulletdrop.com` - Screenshots (5MB limit)
- `cdn.bulletdrop.com` - CDN (50MB limit, premium)
- `media.bulletdrop.com` - Large media (100MB limit, premium)

### API Integration

#### Direct API Usage
```bash
# Upload file via API
curl -X POST "http://localhost:8000/api/uploads/sharex" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "file=@image.png"
```

#### Response Format
```json
{
  "url": "http://localhost:8000/static/images/file.png",
  "thumbnail_url": "http://localhost:8000/static/images/file.png",
  "deletion_url": "http://localhost:8000/api/uploads/123/delete"
}
```

#### Authentication
- JWT tokens required for all upload operations
- Tokens obtained through login/registration
- Include in Authorization header: `Bearer YOUR_TOKEN`

### Analytics and Tracking

#### View Counting
- Automatic view tracking for public file access
- View counts displayed in uploads table
- No tracking for file owner access

#### Upload Statistics
- Total uploads count
- Storage usage tracking
- Upload history with timestamps

---

## 🔧 Troubleshooting

### Common Issues

#### 401 Unauthorized Error
**Problem**: ShareX/Flameshot upload fails with 401 error
**Solution**:
1. Check JWT token is correct and not expired
2. Re-login to get fresh token
3. Update ShareX/Flameshot configuration

#### 413 File Too Large
**Problem**: Upload fails with file too large error
**Solution**:
1. Check file size (default limit: 10MB)
2. Compress images before upload
3. Use premium domain with higher limits

#### 400 Bad Request - File Type
**Problem**: Upload fails with file type error
**Solution**:
1. Check file extension is allowed
2. Rename file with proper extension
3. Contact admin for additional file type support

#### Frontend Login Issues
**Problem**: Can't login or registration fails
**Solution**:
1. Check backend server is running (port 8000)
2. Verify database is accessible
3. Check browser console for detailed errors
4. Try different username/email

#### Screenshots Not Uploading
**Problem**: ShareX/Flameshot not uploading
**Solution**:
1. Check JWT token configuration
2. Verify backend server is accessible
3. Test API endpoint manually with curl
4. Check script permissions (Linux)

### Getting Help

#### Check Server Status
```bash
# Test backend health
curl http://localhost:8000/health

# Test authentication
curl -X POST "http://localhost:8000/api/auth/login/json" \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'
```

#### Debug Mode
- Check browser developer tools for frontend errors
- Check backend server logs for API errors
- Enable detailed logging in screenshot scripts

#### Support Resources
- API Documentation: http://localhost:8000/docs
- Backend logs: Check terminal running uvicorn
- Frontend logs: Browser developer console
- Screenshot tool logs: Check script output

---

## 🎉 Success Indicators

You know everything is working correctly when:

✅ **Registration/Login**: Can create account and login successfully
✅ **Web Upload**: Drag-and-drop works, shows progress, copies URL
✅ **Screenshots**: ShareX/Flameshot uploads automatically
✅ **File Access**: URLs work in browser, files load correctly
✅ **Management**: Can view, copy, and delete uploads
✅ **Storage**: Dashboard shows accurate storage usage
✅ **Clipboard**: URLs automatically copied for easy sharing

---

## 🎯 Next Steps

After mastering the basics:

1. **Configure Custom Domains**: Set up your own domains for professional links
2. **Automate Workflows**: Create scripts for bulk uploads or integrations
3. **Monitor Usage**: Track analytics and optimize storage usage
4. **Share with Team**: Set up accounts for team members
5. **Production Setup**: Deploy to production server with HTTPS

Happy uploading! 🚀