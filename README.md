# macOS UI Automation System

A sophisticated UI automation system for macOS that uses AI to interpret natural language commands and execute them through UI interactions.

## Features

- Natural language command interpretation
- Grid-based UI element targeting
- Four core action types:
  - TYPE: Text input
  - CLICK: UI element interaction
  - HOTKEY: Keyboard shortcuts
  - TERMINAL: Command execution
- Real-time visual verification
- Automated application launching and window management
- Screenshot-based action verification

## Requirements

- macOS
- Python 3.8+
- PySide6
- Google Gemini API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/omarmaaroufoffice/impddd.git
cd impddd
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Gemini API key:
```bash
GEMINI_API_KEY=your_api_key_here
```

## Usage

Run the main script:
```bash
python3 src/main.py
```

The system will display two windows:
1. Control Window: For entering commands and viewing execution status
2. Grid Overlay: For visualizing UI element targeting

## Architecture

- `src/ai_controller.py`: Main controller for AI-driven automation
- `src/ai_control_window.py`: UI interface for command input and status display
- `src/screen_mapper.py`: Grid overlay system for UI element targeting

## License

MIT License