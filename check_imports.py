#!/usr/bin/env python3
"""Test script to verify Python imports and paths."""
import sys
import os

print("Python sys.path:")
for p in sys.path:
    print(f"- {p}")

print("\nTesting imports:")
try:
    print("Importing core_config...")
    import core_config
    print(f"Success! core_config location: {core_config.__file__}")
    
    print("\nTesting Django settings...")
    from django.conf import settings
    print(f"Django settings module: {settings.SETTINGS_MODULE}")
    print(f"Installed apps: {settings.INSTALLED_APPS}")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("\nCurrent working directory:", os.getcwd())
    print("\nDirectory contents:")
    for item in os.listdir('.'):
        print(f"- {item}" + (" (dir)" if os.path.isdir(item) else ""))
