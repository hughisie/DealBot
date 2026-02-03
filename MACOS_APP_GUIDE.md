# 🍎 DealBot macOS App - Installation Complete!

## ✅ **What's Done**

DealBot is now a **native macOS application** with:
- ✅ Custom icon (blue circle with % symbol)
- ✅ Installed in `/Applications/DealBot.app`
- ✅ Appears in **Launchpad**
- ✅ Appears in **Spotlight** search
- ✅ Full macOS app bundle with proper signing

---

## 🚀 **How to Launch**

### **Method 1: Launchpad** (Easiest)
1. Open **Launchpad** (F4 or pinch on trackpad)
2. Find **DealBot** icon (blue circle with % symbol)
3. Click to launch!

### **Method 2: Spotlight**
1. Press `⌘ + Space`
2. Type "DealBot"
3. Press Enter

### **Method 3: Applications Folder**
1. Open **Finder**
2. Go to **Applications**
3. Double-click **DealBot**

### **Method 4: Dock** (Optional)
1. Launch DealBot using any method above
2. Right-click the icon in Dock
3. Options → Keep in Dock

---

## 🎨 **The Icon**

Your DealBot icon features:
- 🔵 Blue circular background
- ⚡ White percentage (%) symbol
- 📱 Modern, clean design
- 🎯 Instantly recognizable in Launchpad

Icon files are located in:
- `resources/icon.png` (main)
- `resources/icon-*.png` (various sizes)

---

## 📂 **App Structure**

```
/Applications/DealBot.app/
├── Contents/
│   ├── MacOS/
│   │   └── DealBot (executable)
│   ├── Resources/
│   │   ├── dealbot.icns (icon)
│   │   ├── app/ (your code)
│   │   └── support/ (Python runtime)
│   └── Info.plist (app metadata)
```

---

## 🔧 **Configuration**

The app uses your existing configuration:
- **Config file**: `config.yaml` (in project directory)
- **Environment**: Reads from your shell environment
- **Database**: `dealbot.db` (in project directory)

**Important**: The app runs from the **project directory**, not from `/Applications/`.

---

## 🛠️ **Rebuilding the App**

If you make code changes, rebuild with:

```bash
# Navigate to project
cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"

# Rebuild app
./venv/bin/briefcase build macOS

# Reinstall (overwrites existing)
cp -r build/dealbot/macos/app/DealBot.app /Applications/

# Refresh Dock/Launchpad
killall Dock
```

Or use the quick rebuild script:

```bash
# Create rebuild script
cat > rebuild_app.sh << 'EOF'
#!/bin/bash
cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"
echo "🔨 Building DealBot..."
./venv/bin/briefcase build macOS
echo "📦 Installing to /Applications..."
cp -r build/dealbot/macos/app/DealBot.app /Applications/
echo "🔄 Refreshing Dock..."
killall Dock
echo "✅ Done! Launch DealBot from Launchpad"
EOF

chmod +x rebuild_app.sh
./rebuild_app.sh
```

---

## 🎯 **Update the Icon**

To change the icon design:

1. **Edit** `create_icon.py` (colors, design, etc.)
2. **Regenerate icons**:
   ```bash
   ./venv/bin/python create_icon.py
   ```
3. **Rebuild app**:
   ```bash
   ./venv/bin/briefcase build macOS
   cp -r build/dealbot/macos/app/DealBot.app /Applications/
   killall Dock
   ```

---

## 📱 **App Features**

The macOS app includes all DealBot features:
- ✅ Load TXT files with deals
- ✅ Preview with images, prices, ratings
- ✅ 48-hour duplicate detection
- ✅ Clear deals button
- ✅ Manual override toggles
- ✅ WhatsApp publishing
- ✅ Database tracking
- ✅ Status logging

---

## 🚨 **Troubleshooting**

### **App won't open / "damaged" error**
```bash
# Remove quarantine flag
xattr -cr /Applications/DealBot.app
```

### **Icon not showing in Launchpad**
```bash
# Force rebuild Launchpad database
defaults write com.apple.dock ResetLaunchPad -bool true
killall Dock
```

### **App crashes on launch**
Check the logs:
```bash
# View console logs
log show --predicate 'process == "DealBot"' --info --last 5m
```

### **Configuration not found**
The app looks for config in the **project directory**, not `/Applications/`. Make sure:
- `config.yaml` exists in project root
- Environment variables are set (add to `~/.zshrc` or `~/.bash_profile`)

---

## 🔐 **App Signing**

The app is **ad-hoc signed** automatically by Briefcase. This means:
- ✅ Works on your Mac
- ✅ Can be shared via direct file transfer
- ⚠️ Not notarized (can't distribute via download without Gatekeeper warnings)

For **distribution**, you'd need:
1. Apple Developer account ($99/year)
2. Developer certificate
3. App notarization

---

## 📦 **Distribution Options**

### **Option 1: Direct Copy** (Current)
- Copy `DealBot.app` to another Mac
- Run `xattr -cr DealBot.app` on target Mac
- Move to `/Applications/`

### **Option 2: DMG Installer**
```bash
./venv/bin/briefcase package macOS
# Creates a DMG in dist/ folder
```

### **Option 3: Mac App Store**
- Requires Apple Developer account
- Full app review process
- Need to add sandbox entitlements

---

## 🎊 **Success!**

Your DealBot is now a **professional macOS application**! 🎉

### **Key Achievements:**
✅ Native macOS app bundle  
✅ Custom blue icon with % symbol  
✅ Installed in Applications  
✅ Appears in Launchpad  
✅ Searchable in Spotlight  
✅ Easy to launch and use  

### **Next Steps:**
1. Open **Launchpad**
2. Find the blue **DealBot** icon
3. Click to launch
4. Start processing deals!

**Enjoy your professional macOS deal publishing app! 🚀**

---

## 📝 **Files Created**

- `pyproject.toml` - Briefcase configuration
- `create_icon.py` - Icon generator script
- `resources/icon*.png` - Icon files (all sizes)
- `LICENSE` - MIT license
- `dealbot/` - Copy of source for Briefcase
- `build/dealbot/macos/app/DealBot.app` - Built app
- `/Applications/DealBot.app` - Installed app

---

## 🔗 **Quick Links**

- **Project**: `/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot`
- **App**: `/Applications/DealBot.app`
- **Config**: `config.yaml`
- **Database**: `dealbot.db`
- **Briefcase Docs**: https://briefcase.readthedocs.io
