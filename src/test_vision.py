#!/usr/bin/env python3

import sys
import logging
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ai_controller import AIController

def run_vision_tests():
    """Run comprehensive vision and click accuracy tests"""
    app = QApplication(sys.argv)
    
    # Initialize the controller
    controller = AIController()
    
    # Create a timer to start tests after UI is fully initialized
    def start_tests():
        print("\nPreparing Vision Tests...")
        print("------------------------")
        
        # First ensure grid overlay is visible
        if controller.window and controller.screen_mapper:
            print("Showing grid overlay...")
            controller.window.grid_toggle.setChecked(True)
            controller.window.toggle_grid()
            
            # Wait for grid to be fully visible
            time.sleep(2)
            
            # Capture initial screenshot with grid
            print("Capturing initial screenshot with grid overlay...")
            initial_screenshot = controller.capture_grid_screenshot()
            if initial_screenshot:
                initial_screenshot.save("screenshots/initial_grid_overlay.png")
                print("✓ Grid overlay screenshot saved")
            else:
                print("✗ Failed to capture grid overlay")
                return
            
            # Now run the tests
            print("\n1. Running Click Accuracy Test...")
            results = controller.test_click_accuracy()
            if results:
                success_count = sum(1 for r in results if r.get("success", False))
                total = len(results)
                print(f"Click Accuracy Results: {success_count}/{total} successful clicks")
                
                # Print detailed results
                for result in results:
                    coord = result.get("coordinate")
                    pos = result.get("position")
                    success = "✓" if result.get("success") else "✗"
                    print(f"{success} {coord} ({pos})")
            
            # 2. Grid Coordinate Test
            print("\n2. Running Grid Coordinate Test...")
            valid_coords, invalid_coords = controller.test_grid_coordinates()
            print(f"Grid Test Results: {len(valid_coords)} valid, {len(invalid_coords)} invalid coordinates")
            
            if invalid_coords:
                print("Invalid coordinates found:", ", ".join(invalid_coords[:10]))
                if len(invalid_coords) > 10:
                    print(f"...and {len(invalid_coords) - 10} more")
            
            # 3. Visual Verification Test
            print("\n3. Running Visual Verification Tests...")
            test_coords = ["aa01", "an01", "aa20", "ah20", "an40"]
            for coord in test_coords:
                # Ensure grid is visible for each verification
                controller.window.grid_toggle.setChecked(True)
                controller.window.toggle_grid()
                time.sleep(0.5)  # Wait for grid to be visible
                
                result = controller.verify_click_position(coord)
                print(f"Verifying {coord}: {'✓' if result else '✗'}")
                
                # Save verification screenshot
                verification_screenshot = controller.capture_grid_screenshot()
                if verification_screenshot:
                    verification_screenshot.save(f"screenshots/verify_{coord}.png")
            
            print("\nTests completed. Check the screenshots directory for visual results:")
            print("- initial_grid_overlay.png: Initial grid overlay state")
            print("- click_accuracy_visualization.png: Click accuracy test results")
            print("- verify_*.png: Individual coordinate verification results")
            print("\nYou can close the application now.")
        else:
            print("Error: Controller windows not properly initialized")
    
    # Start tests after a short delay to ensure UI is ready
    QTimer.singleShot(1000, start_tests)
    
    return app.exec()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ensure screenshots directory exists
    Path("screenshots").mkdir(exist_ok=True)
    
    sys.exit(run_vision_tests()) 