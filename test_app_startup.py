#!/usr/bin/env python3
"""Test script to debug DealBot startup issues."""

import sys
import os

# Add app paths
sys.path.insert(0, '/Applications/DealBot.app/Contents/Resources/app')
sys.path.insert(0, '/Applications/DealBot.app/Contents/Resources/app_packages')

# Change to app resource directory
os.chdir('/Applications/DealBot.app/Contents/Resources')

print("=" * 60)
print("Testing DealBot Startup")
print("=" * 60)

try:
    print("\n1. Importing dealbot.app...")
    from dealbot.app import main, DealBot
    print("   ✅ Import successful")
    
    print("\n2. Creating app instance...")
    app = main()
    print(f"   ✅ App created: {app}")
    print(f"   - formal_name: {app.formal_name}")
    print(f"   - app_id: {app.app_id}")
    
    print("\n3. Calling startup()...")
    app.startup()
    print("   ✅ Startup completed")
    
    print("\n4. Checking main_window...")
    if hasattr(app, 'main_window'):
        print(f"   ✅ main_window exists: {app.main_window}")
        print(f"   - title: {app.main_window.title}")
        print(f"   - visible: {app.main_window.visible}")
    else:
        print("   ❌ main_window not created")
    
    print("\n5. Starting main_loop() - press Ctrl+C to exit...")
    # Don't actually start the loop in test mode
    # app.main_loop()
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("Test completed successfully!")
print("=" * 60)
