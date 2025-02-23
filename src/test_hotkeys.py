import subprocess
import time
import logging

logging.basicConfig(level=logging.DEBUG)

class HotkeyTester:
    def __init__(self):
        self.ACTION_DELAY = 0.1
        self.HOTKEY_DELAY = 0.1
        
        # Define macOS hotkeys for testing
        self.HOTKEYS = {
            "spotlight": ("command", "space"),
            "enter": ("return",),
            "escape": ("escape",),
            "tab": ("tab",),
        }

    def _get_key_code_map(self):
        return {
            "return": 36,
            "tab": 48,
            "space": 49,
            "delete": 51,
            "escape": 53,
            "command": 55,
            "shift": 56,
            "option": 58,
            "control": 59,
        }

    def _get_key_code(self, key):
        return self._get_key_code_map().get(key, 0)

    def execute_hotkey(self, hotkey_name):
        if hotkey_name not in self.HOTKEYS:
            raise ValueError(f"Unknown hotkey: {hotkey_name}")
            
        keys = self.HOTKEYS[hotkey_name]
        
        try:
            # Special handling for Command+Space (Spotlight)
            if hotkey_name == "spotlight":
                applescript = '''
                tell application "System Events"
                    delay 0.2
                    key code 49 using {command down}
                    delay 0.2
                end tell
                '''
            # Handle special single keys
            elif len(keys) == 1:
                key = keys[0]
                if key in self._get_key_code_map():
                    key_code = self._get_key_code(key)
                    applescript = f'''
                    tell application "System Events"
                        delay {self.ACTION_DELAY}
                        key code {key_code}
                        delay {self.ACTION_DELAY}
                    end tell
                    '''
                else:
                    applescript = f'''
                    tell application "System Events"
                        delay {self.ACTION_DELAY}
                        keystroke "{key}"
                        delay {self.ACTION_DELAY}
                    end tell
                    '''
            else:
                # Handle other modifier key combinations
                modifiers = []
                for key in keys[:-1]:
                    if key == "command":
                        modifiers.append("command down")
                    elif key == "shift":
                        modifiers.append("shift down")
                    elif key == "option":
                        modifiers.append("option down")
                    elif key == "control":
                        modifiers.append("control down")
                
                modifier_str = ", ".join(modifiers)
                final_key = keys[-1]
                
                applescript = f'''
                tell application "System Events"
                    keystroke "{final_key}" using {{{modifier_str}}}
                end tell
                '''

            print(f"Executing AppleScript:\n{applescript}")
            subprocess.run(["osascript", "-e", applescript], check=True)
            logging.debug("Executed hotkey successfully: %s", hotkey_name)
            return True
        except subprocess.CalledProcessError as e:
            logging.exception("Failed to execute hotkey %s: %s", hotkey_name, e)
            raise Exception(f"Failed to execute hotkey {hotkey_name}: {str(e)}")

    def test_hotkeys(self):
        test_keys = [
            "spotlight",  # Command+Space
            "enter",      # Return key
            "escape",     # Escape key
            "tab",        # Tab key
        ]
        
        results = []
        for key in test_keys:
            try:
                print(f"\nTesting hotkey: {key}")
                success = self.execute_hotkey(key)
                results.append(f"✓ {key}: Success")
                time.sleep(1)  # Wait between tests
            except Exception as e:
                results.append(f"✗ {key}: Failed - {str(e)}")
        
        return "\n".join(results)

    def test_spotlight_terminal(self):
        """Test opening Terminal using Spotlight (Command+Space)"""
        try:
            print("\nTesting opening Terminal via Spotlight...")
            
            # Open Spotlight with a more reliable approach
            print("1. Opening Spotlight...")
            applescript = '''
            tell application "System Events"
                delay 0.2
                key code 49 using {command down}
                delay 0.3
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript], check=True)
            
            # Type "terminal" with delay between characters
            print("2. Typing 'terminal'...")
            applescript = '''
            tell application "System Events"
                delay 0.1
                keystroke "terminal"
                delay 0.2
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript], check=True)
            
            # Press Enter and wait for Terminal
            print("3. Pressing Enter...")
            applescript = '''
            tell application "System Events"
                key code 36
                delay 1.0
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript], check=True)
            
            # Verify Terminal is running
            print("4. Verifying Terminal launched...")
            applescript = '''
            tell application "System Events"
                return exists (process "Terminal")
            end tell
            '''
            result = subprocess.run(["osascript", "-e", applescript], 
                                  capture_output=True, text=True, check=True)
            
            if result.stdout.strip() == "true":
                print("✓ Terminal launched successfully")
                return True
            else:
                print("✗ Terminal failed to launch")
                return False
                
        except Exception as e:
            print(f"✗ Test failed: {str(e)}")
            return False

if __name__ == "__main__":
    print("Starting hotkey tests...")
    tester = HotkeyTester()
    print("\nTesting Terminal launch via Spotlight:")
    tester.test_spotlight_terminal()
    results = tester.test_hotkeys()
    print("\nTest Results:")
    print(results) 