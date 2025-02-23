# Project Requirements for macOS UI Automation System

## Dependencies
- Python 3.8+
- PySide6 (Qt for Python)
- Pillow (PIL)
- mss
- google-genai (or simulated version)
- pynput
- python-dotenv

## System Requirements
- **Operating System:** macOS
- **Hardware:** Standard macOS hardware; no extra requirements.

## Environment Variables
- **GEMINI_API_KEY:** Your API key for the Gemini AI service.
- **WORKSPACE_ROOT:** Path to the workspace directory for saving outputs.

## Setup Prerequisites
- Install Python 3.8 or above.
- Use pip to install dependencies (see `requirements.txt`).

## Known Limitations or Issues
- The system is currently designed for macOS only.
- AI responses are simulated if the real API is not available.
- Error recovery is implemented, but further robustness testing is needed.

## Future Improvements
- Enhance error recovery and logging.
- Extend support to other operating systems.
- Integrate with real AI services (e.g., updated Gemini models).

## Security Considerations
- Ensure API keys are securely stored.
- Validate all user inputs to prevent unauthorized actions.

## Performance Requirements
- Optimize screenshot caching to avoid performance delays.
- Ensure asynchronous processing does not block the UI.

## Missing Features
- Full integration with production AI models.
- Advanced security mechanisms.