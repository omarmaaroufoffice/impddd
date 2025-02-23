"""
ai_control_window.py

This module defines the AIControlWindow class, which is the main UI window for the macOS UI Automation System.
The window provides controls for user commands and displays real-time status updates.
It utilizes PySide6 for UI components and manages asynchronous updates from the AIWorker thread.

Classes:
    AIControlWindow: QMainWindow subclass providing the primary user interface.
"""

import sys
import time
import logging
from PySide6.QtCore import Qt, QTimer, QMetaObject, Q_ARG, Slot, Signal
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QLineEdit, QPushButton, QLabel, QTextEdit,
                               QMessageBox, QApplication, QSizePolicy)
from PySide6.QtCore import QThread

class AIControlWindow(QMainWindow):
    """
    AIControlWindow implements the primary user interface for the automation system.

    Features:
        - Input field for high-level tasks
        - A button to execute tasks
        - A status display panel that shows real-time logs and AI responses
        - Real-time updates from an AIWorker thread
    """
    show_message_signal = Signal(str, str)

    def __init__(self, controller):
        """
        Initialize the control window with its layout, widgets, and timers.

        Args:
            controller (AIController): Instance of the main automation controller.
        """
        super().__init__()
        self.controller = controller
        self.worker = None
        self.update_queue = []
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(100)  # Update every 100ms
        self.update_timer.timeout.connect(self.refresh_display)
        self.update_timer.start()
        self.initUI()
        self.execute_timer = QTimer(self)
        self.execute_timer.setSingleShot(True)
        self.execute_timer.timeout.connect(self._execute_action)
        screen_geom = self.controller.screen_mapper.screen.geometry() if self.controller.screen_mapper else None
        if screen_geom:
            self.move(20, 20)
        self.setMinimumSize(600, 400)  # Reduced window size since we removed screenshots
        self.show()  # Make sure window is visible
        logging.info("AIControlWindow initialized.")
        self.show_message_signal.connect(self._show_message_on_main_thread)

    def initUI(self):
        """
        Set up the user interface components of the control window.
        """
        self.setWindowTitle("AI Screen Control")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        # Create and set the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Add instruction label
        instruction = QLabel("Enter what you want the AI to do:\n(The grid window will stay open for reference)")
        instruction.setWordWrap(True)
        instruction.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(instruction)

        # Add input field
        self.input_field = QLineEdit()
        self.input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_field.setPlaceholderText("Type your task here and press Enter")
        self.input_field.returnPressed.connect(self.execute_action)
        layout.addWidget(self.input_field)

        # Add execute button
        execute_btn = QPushButton("Execute Task")
        execute_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        execute_btn.clicked.connect(self.execute_action)
        layout.addWidget(execute_btn)

        # Add status display
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.status_display.setAcceptRichText(True)
        layout.addWidget(self.status_display)

        # Set the window style
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QWidget { background-color: #2b2b2b; color: #ffffff; font-size: 12px; }
            QLabel { font-size: 13px; color: #ffffff; padding: 5px; }
            QLineEdit { padding: 8px; border: 1px solid #555555; border-radius: 3px; background-color: #363636; font-size: 14px; margin: 5px 0; }
            QPushButton { padding: 10px; background-color: #0066cc; border: none; border-radius: 3px; font-size: 14px; margin: 5px 0; }
            QPushButton:hover { background-color: #0077ee; }
            QTextEdit { border: 1px solid #555555; border-radius: 3px; background-color: #363636; padding: 10px; font-family: monospace; font-size: 12px; line-height: 1.5; margin: 5px 0; }
        """)
        
        # Ensure the window is visible
        self.show()
        
        logging.info("UI components initialized in AIControlWindow.")

    @Slot()
    def refresh_display(self):
        """
        Refresh the status display with pending updates.
        """
        try:
            if self.update_queue:
                for update in self.update_queue:
                    if isinstance(update, str):
                        self.status_display.append(update)
                    elif isinstance(update, dict) and "type" in update:
                        if update["type"] == "task":
                            self._display_task_update(update)
                        elif update["type"] == "response":
                            self._display_ai_response(update)
                        elif update["type"] == "error":
                            self._display_error(update)
                self.update_queue.clear()
                scrollbar = self.status_display.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
                QApplication.processEvents()
        except Exception as e:
            logging.exception("Error refreshing display: %s", e)

    def _display_task_update(self, update):
        """Display a task update in the status display."""
        try:
            step = update.get("step", "")
            status = update.get("status", "")
            details = update.get("details", "")
            if status == "start":
                self.status_display.append(f"\n📍 Step: {step}")
            elif status == "success":
                self.status_display.append(f"✓ {details}")
            elif status == "failure":
                self.status_display.append(f"✗ {details}")
            elif status == "progress":
                self.status_display.append(f"⏳ {details}")
        except Exception as e:
            logging.exception("Error in task update display: %s", e)

    def _display_ai_response(self, update):
        """Display an AI response update."""
        try:
            response_type = update.get("response_type", "")
            response = update.get("response", "")
            if response_type == "plan":
                self.status_display.append("\n🤖 <b>AI Planning Response:</b>")
                if isinstance(response, dict):
                    if "raw_response" in response:
                        self.status_display.append("\n<i>Raw Response:</i>")
                        self.status_display.append(response["raw_response"])
                    if "processed_steps" in response:
                        self.status_display.append("\n<i>Processed Steps:</i>")
                        for step in response["processed_steps"]:
                            self.status_display.append(f"• {step}")
                else:
                    for step in response:
                        self.status_display.append(f"• {step}")
            elif response_type == "verification":
                self.status_display.append("\n🔍 <b>AI Verification Response:</b>")
                if isinstance(response, dict):
                    result = response.get("result", "")
                    details = response.get("details", "")
                    icon = "✓" if result == "SUCCESS" else "?" if result == "UNCLEAR" else "✗"
                    self.status_display.append(f"\n<i>Result:</i> {icon} {result}")
                    if details:
                        self.status_display.append(f"  Details: {details}")
            elif response_type == "execution":
                self.status_display.append("\n🎯 <b>AI Execution Response:</b>")
                if isinstance(response, dict):
                    if "action" in response:
                        self.status_display.append(f"\n<i>Action:</i> {response['action']}")
                    if "attempt" in response:
                        self.status_display.append(f"  Attempt: {response['attempt']}")
        except Exception as e:
            logging.exception("Error displaying AI response: %s", e)

    def _display_error(self, update):
        """Display errors in the status display."""
        try:
            error_msg = update.get("error", "Unknown error")
            self.status_display.append(f"\n❌ Error: {error_msg}")
        except Exception as e:
            logging.exception("Error displaying error message: %s", e)

    @Slot()
    def hide_active_dialogs(self):
        """Hide any active message boxes or dialogs."""
        if QThread.currentThread() != QApplication.instance().thread():
            QMetaObject.invokeMethod(self, "hide_active_dialogs", Qt.QueuedConnection)
            return
            
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                widget.hide()

    @Slot(str, str)
    def _show_message_on_main_thread(self, title, message):
        """Show message box on the main thread."""
        if QThread.currentThread() != QApplication.instance().thread():
            self.show_message_signal.emit(title, message)
            return
            
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        result = msg_box.exec()
        
        self.controller.last_verification_result = (result == QMessageBox.Yes)
        
        if hasattr(self.controller, 'user_verification_event'):
            self.controller.user_verification_event.set()
        
        return self.controller.last_verification_result

    def show_message(self, title, message):
        """Thread-safe way to show a message box."""
        return self._show_message_on_main_thread(title, message)

    @Slot(str)
    def update_status(self, message):
        """Queue a status update message."""
        self.update_queue.append(message)

    @Slot(dict)
    def queue_task_update(self, update):
        """Queue an update related to task execution."""
        update["type"] = "task"
        self.update_queue.append(update)

    @Slot(dict)
    def queue_ai_response(self, response):
        """Queue an AI response update message."""
        response["type"] = "response"
        self.update_queue.append(response)

    @Slot(str)
    def queue_error(self, error):
        """Queue an error message."""
        self.update_queue.append({
            "type": "error",
            "error": error
        })

    def execute_action(self):
        """Debounce and trigger task execution from the input field."""
        self.execute_timer.start(5000)  # Changed to 5000ms (5 seconds)
        self.status_display.clear()
        self.status_display.append("⏳ <b>Starting in 5 seconds...</b>")
        
        # Create countdown timer
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)  # 1 second intervals
        self.countdown_remaining = 4  # Start at 4 since we already showed 5
        
        def update_countdown():
            if self.countdown_remaining > 0:
                self.status_display.append(f"⏳ Starting in {self.countdown_remaining} seconds...")
                self.countdown_remaining -= 1
            else:
                self.countdown_timer.stop()
        
        self.countdown_timer.timeout.connect(update_countdown)
        self.countdown_timer.start()

    def _execute_action(self):
        """Internal method called after delay to start the worker thread."""
        request = self.input_field.text().strip()
        if not request:
            return
        
        self.status_display.clear()
        self.status_display.append("🎯 <b>Task History</b>")
        self.status_display.append("-------------------")
        self.status_display.append(f"\n📋 <b>New Task:</b> {request}")
        
        # Import AIWorker here to avoid circular imports
        from ai_controller import AIWorker
        
        self.worker = AIWorker(self.controller, request)
        self.worker.progress.connect(self.update_status)
        self.worker.task_update.connect(self.queue_task_update)
        self.worker.ai_response.connect(self.queue_ai_response)
        self.worker.error.connect(self.queue_error)
        self.worker.finished.connect(self.handle_results)
        self.worker.show_message.connect(self.show_message)
        self.worker.start()
        self.input_field.setEnabled(False)

    def handle_results(self, results):
        """Process and display results once the AIWorker completes execution."""
        self.status_display.append("\n✓ <b>Task Completed</b>")
        self.status_display.append("\n📊 <b>Results by Step:</b>")
        for result in results:
            step = result.get("step", "")
            if "error" in result:
                self.status_display.append(f"\n❌ Step: {step}")
                self.status_display.append(f"   Error: {result.get('error')}")
            else:
                coord = result.get("coordinate", "")
                verif = result.get("verification", "")
                icon = "✓" if verif == "SUCCESS" else "?" if verif == "UNCLEAR" else "✗"
                self.status_display.append(f"\n{icon} Step: {step}")
                self.status_display.append(f"   Coordinate: {coord}")
                self.status_display.append(f"   Result: {verif}")
        successes = sum(1 for r in results if r.get("verification") == "SUCCESS")
        failures = sum(1 for r in results if r.get("verification") == "FAILURE")
        unclear = sum(1 for r in results if r.get("verification") == "UNCLEAR")
        errors = sum(1 for r in results if "error" in r)
        self.status_display.append("\n📈 <b>Summary:</b>")
        self.status_display.append(f"✓ Successful steps: {successes}")
        self.status_display.append(f"✗ Failed steps: {failures}")
        self.status_display.append(f"? Unclear steps: {unclear}")
        self.status_display.append(f"⚠️ Errors: {errors}")
        self.input_field.setEnabled(True)

# End of AIControlWindow module.