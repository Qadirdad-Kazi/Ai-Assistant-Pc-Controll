# 🔧 Wolf AI - Utilities & Helper Tools

This directory contains utility scripts and helper tools for managing Wolf AI.

## 📁 Files

### 🖼️ `check_icons.py` - Icon Validation Tool
**Purpose**: Validates that all required GUI icons are present and accessible

#### What it does:
- 🔍 **Scans GUI Components** - Checks all icon references
- ✅ **Validates Files** - Ensures icon files exist
- 📊 **Reports Status** - Shows which icons are missing
- 🛠️ **Helps Debug** - Aids in GUI troubleshooting

#### How to Use:
```bash
# Check all GUI icons
python utilities/check_icons.py

# You'll see output like:
# ✅ Icon found: gui/assets/logo.png
# ✅ Icon found: gui/assets/light_on.png
# ❌ Missing: gui/assets/custom_icon.png
# 📊 Total icons: 25, Missing: 1
```

#### What it Checks:
- 📁 **GUI Assets** - All icon files in gui/assets/
- 🎨 **Component Icons** - Icons referenced in GUI code
- 🔗 **File Paths** - Validates file accessibility
- 📏 **File Sizes** - Checks for empty/corrupted files

---

### 📋 `icons.txt` - Icon Inventory List
**Purpose**: Complete inventory of all icons used in Wolf AI

#### What it contains:
- 📝 **Icon Names** - All icon file names
- 📍 **File Paths** - Where each icon is stored
- 🎨 **Usage Info** - Which components use each icon
- 📏 **File Sizes** - Icon file sizes

#### Icon Categories:
```
🏠 Home Icons:
- logo.png (120x120) - Main app logo
- wolf_avatar.png (256x256) - Your branding

🎛️ Control Icons:
- light_on.png (32x32) - Light on state
- light_off.png (32x32) - Light off state
- power_button.png (24x24) - Power controls

📊 Status Icons:
- microphone_on.png (16x16) - Voice active
- thinking.png (32x32) - AI processing
- checkmark.png (16x16) - Success state
```

#### How to Use:
```bash
# View icon inventory
cat utilities/icons.txt

# Search for specific icons
grep "light" utilities/icons.txt

# Count total icons
wc -l utilities/icons.txt
```

---

## 🎯 Utility Use Cases

### 1. **GUI Development**
```bash
# Before adding new icons
python utilities/check_icons.py

# After adding new icons
python utilities/check_icons.py
# Verify new icons appear in the list
```

### 2. **Asset Management**
```bash
# Check what icons you have
cat utilities/icons.txt

# Find missing icons
python utilities/check_icons.py

# Backup important icons
cp gui/assets/*.png backup/icons/
```

### 3. **Troubleshooting**
```bash
# GUI not showing icons?
python utilities/check_icons.py
# Check for missing files in the output

# Icons look distorted?
cat utilities/icons.txt
# Check file sizes for 0-byte files
```

---

## 🛠️ Adding New Icons

### Step 1: Create Icon
```bash
# Create your icon (PNG format, transparent background)
# Recommended sizes: 16x16, 24x24, 32x32, 48x48, 64x64
# Save to: gui/assets/your_icon.png
```

### Step 2: Update Code
```python
# In your GUI component:
from PySide6.QtGui import QIcon
icon = QIcon("gui/assets/your_icon.png")
button.setIcon(icon)
```

### Step 3: Validate
```bash
# Check your new icon is detected
python utilities/check_icons.py

# Should show:
# ✅ Icon found: gui/assets/your_icon.png
```

### Step 4: Update Inventory
```bash
# Add to icons.txt:
echo "your_icon.png (32x32) - Your custom icon" >> utilities/icons.txt
```

---

## 📊 Icon Guidelines

### Technical Requirements:
- 📁 **Format**: PNG with transparency
- 🎨 **Colors**: Work with dark/light themes
- 📏 **Sizes**: Multiple sizes for different UI elements
- 🔍 **Resolution**: Crisp at all display scales

### Design Guidelines:
- 🎯 **Consistency**: Match existing icon style
- 🌙 **Dark Mode**: Ensure visibility on dark backgrounds
- ☀️ **Light Mode**: Ensure visibility on light backgrounds
- ♿ **Accessibility**: Clear, recognizable symbols

### Recommended Sizes:
```
16x16 - Small UI elements (status indicators)
24x24 - Buttons and controls
32x32 - Main action buttons
48x48 - Toolbar icons
64x64 - Large icons and logos
128x128 - Splash screen logos
256x256 - High-DPI displays
```

---

## 🐛 Utility Troubleshooting

### Common Issues:

#### 🔴 "Icons not found"
**Causes**:
- Icon files missing from gui/assets/
- Incorrect file paths in code
- File permission issues

**Solutions**:
```bash
# Check what's missing
python utilities/check_icons.py

# Fix file paths
# Update code to use correct paths

# Fix permissions
chmod 644 gui/assets/*.png
```

#### 🔴 "Icons appear distorted"
**Causes**:
- Wrong icon size for UI element
- Low-resolution source images
- Scaling issues

**Solutions**:
```bash
# Check icon sizes
file gui/assets/problem_icon.png

# Replace with correct size
# Use appropriate size for UI element
```

#### 🔴 "Icons not updating"
**Causes**:
- GUI cache not cleared
- Icon files not saved properly
- Application needs restart

**Solutions**:
```bash
# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Restart application
python main.py
```

---

## 📈 Icon Performance

### Optimization Tips:
```bash
# Optimize PNG file sizes
# Use tools like pngcrush or optipng
pngcrush gui/assets/*.png

# Remove unnecessary metadata
# Keep files small for faster loading

# Use appropriate sizes
# Don't use 256x256 for 16x16 display
```

### Performance Impact:
- 🚀 **Small Icons** (<1KB each) - Fast loading
- 🐌 **Large Icons** (>10KB each) - Slower startup
- 📊 **Total Icon Budget** - Aim for <500KB total

---

## 🎨 Custom Icon Themes

### Creating Custom Themes:
```bash
# Create theme directory
mkdir gui/assets/dark_theme/
mkdir gui/assets/light_theme/

# Add themed icons
cp your_dark_icons/* gui/assets/dark_theme/
cp your_light_icons/* gui/assets/light_theme/

# Update code to load theme-specific icons
```

### Theme Switching:
```python
# In your GUI code:
if theme == "dark":
    icon_path = "gui/assets/dark_theme/icon.png"
else:
    icon_path = "gui/assets/light_theme/icon.png"
icon = QIcon(icon_path)
```

---

## 📋 Icon Maintenance

### Regular Tasks:
```bash
# Monthly: Check for missing icons
python utilities/check_icons.py

# Quarterly: Optimize icon sizes
# Review and compress large icons

# Annually: Update icon inventory
# Update icons.txt with new additions
```

### Backup Strategy:
```bash
# Backup all icons
cp -r gui/assets/ backup/icons_$(date +%Y%m%d)/

# Version control important icons
# Add to .gitignore if too many
# Keep custom icons in repo
```

---

These utilities help you maintain Wolf AI's visual appearance and ensure all GUI elements display correctly! 🎨✨
