"""
Diagnostic test for Mission Page
Run this to check if the mission page is being created correctly
"""

import tkinter as tk
from tkinter import messagebox
import sys

try:
    # Add project path
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from gui.pages.mission_page import MissionPage, MISSION_DEFAULTS
    from config.constants import COLORS, FONTS
    
    print("=" * 60)
    print("MISSION PAGE DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Create test window
    root = tk.Tk()
    root.title("Mission Page Test")
    root.geometry("1000x700")
    root.configure(bg=COLORS['bg_dark'])
    
    # Storage dicts
    inputs = {}
    dropdowns = {}
    
    print("\n1. Creating Mission Page...")
    try:
        page = MissionPage(root, inputs, dropdowns)
        print("   ✓ Mission Page created successfully")
    except Exception as e:
        print(f"   ✗ ERROR creating page: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"\n2. Checking created widgets...")
    print(f"   - Input fields created: {len(inputs)}")
    print(f"   - Dropdowns created: {len(dropdowns)}")
    
    if len(inputs) > 0:
        print(f"   ✓ Input fields created")
        print(f"   Sample fields: {list(inputs.keys())[:5]}")
    else:
        print(f"   ✗ WARNING: No input fields created!")
    
    if len(dropdowns) > 0:
        print(f"   ✓ Dropdowns created")
        print(f"   Dropdowns: {list(dropdowns.keys())}")
    else:
        print(f"   ✗ WARNING: No dropdowns created!")
    
    print(f"\n3. Checking page attributes...")
    has_frame = hasattr(page, 'scrollable_frame')
    has_grain_var = hasattr(page, 'grain_preset_var')
    has_tank_var = hasattr(page, 'tank_type_var')
    has_circular_var = hasattr(page, 'circular_var')
    
    print(f"   - Has scrollable_frame: {has_frame}")
    print(f"   - Has grain_preset_var: {has_grain_var}")
    print(f"   - Has tank_type_var: {has_tank_var}")
    print(f"   - Has circular_var: {has_circular_var}")
    
    if all([has_frame, has_grain_var, has_tank_var, has_circular_var]):
        print(f"   ✓ All required attributes present")
    else:
        print(f"   ✗ WARNING: Some attributes missing!")
    
    print(f"\n4. Testing get_mission_data()...")
    try:
        data = page.get_mission_data()
        print(f"   ✓ get_mission_data() works")
        print(f"   Data keys: {list(data.keys())[:10]}")
        print(f"   Sample values:")
        print(f"     - Dport_Dt_optimal: {data.get('Dport_Dt_optimal')}")
        print(f"     - burn_time: {data.get('burn_time')}")
        print(f"     - grain_preset: {data.get('grain_preset')}")
        print(f"     - tank_type: {data.get('tank_type')}")
    except Exception as e:
        print(f"   ✗ ERROR in get_mission_data(): {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n5. Checking widget visibility...")
    if hasattr(page, 'scrollable_frame'):
        children = page.scrollable_frame.winfo_children()
        print(f"   - Number of child widgets in scrollable_frame: {len(children)}")
        if len(children) > 0:
            print(f"   ✓ Widgets are present in scrollable frame")
            for i, child in enumerate(children[:5]):
                print(f"     Widget {i}: {child.winfo_class()}")
        else:
            print(f"   ✗ WARNING: No widgets in scrollable frame!")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_ok = (
        len(inputs) > 0 and
        len(dropdowns) > 0 and
        has_frame and
        has_grain_var and
        has_tank_var and
        has_circular_var
    )
    
    if all_ok:
        print("✓ All tests PASSED - Mission Page should be working")
        print("\nThe window will stay open for 5 seconds so you can see the page.")
        print("If you see widgets on screen, the page is working correctly!")
    else:
        print("✗ Some tests FAILED - Please check the errors above")
    
    print("=" * 60)
    
    # Keep window open for inspection
    root.after(5000, root.destroy)
    root.mainloop()
    
except Exception as e:
    print(f"\nFATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
