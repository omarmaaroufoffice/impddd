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
                               QMessageBox, QApplication, QSizePolicy, QHBoxLayout)
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QCursor
from PySide6.QtCore import QThread, QPoint

class GridOverlayWindow(QWidget):
    """
    A transparent window that displays a permanent orange grid overlay.
    The grid is 40x40 and stays on top of all windows.
    """
    def __init__(self):
        super().__init__()
        # Make the window frameless, stay on top, and transparent to mouse events
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
        # Make the window background transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Make the window ignore mouse events
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Get screen dimensions
        screen = QApplication.primaryScreen()
        self.screen_geometry = screen.geometry()
        self.setGeometry(self.screen_geometry)
        
        # Grid properties
        self.grid_size = 40  # 40x40 grid
        self.cell_width = self.screen_geometry.width() // self.grid_size
        self.cell_height = self.screen_geometry.height() // self.grid_size
        
        # Store current mouse position for hover effects
        self.current_mouse_pos = None
        
        # Set up timer for periodic updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_mouse_position)
        self.update_timer.start(100)  # Update every 100ms
        
        # Show the window
        self.show()

    def check_mouse_position(self):
        """Update mouse position and trigger repaint only when position changes"""
        new_pos = QCursor.pos()  # Use global cursor position since we're transparent to mouse events
        if self.current_mouse_pos != new_pos:
            self.current_mouse_pos = new_pos
            self.update()

    def get_column_label(self, index):
        """Convert numeric index to two-letter column label (aa-na)"""
        # Only use letters a through n
        if index >= 14:  # After 'n', return 'na'
            return 'na'
        first_letter = chr(ord('a') + index)
        second_letter = 'a'
        return f"{first_letter}{second_letter}"

    def paintEvent(self, event):
        """Draw the semi-transparent grid overlay with cross pattern and coordinate system."""
        try:
            painter = QPainter(self)
            try:
                painter.setRenderHint(QPainter.Antialiasing)
                
                # Draw all grid lines with very light opacity (10%)
                grid_pen = QPen(QColor(255, 140, 0, 25))  # Reduced opacity for grid lines
                grid_pen.setWidth(1)
                painter.setPen(grid_pen)
                
                # Draw vertical grid lines
                for x in range(0, self.width(), self.cell_width):
                    painter.drawLine(x, 0, x, self.height())
                
                # Draw horizontal grid lines
                for y in range(0, self.height(), self.cell_height):
                    painter.drawLine(0, y, self.width(), y)
                
                # Set up font for labels with reduced opacity
                font = QFont("Menlo", 9, QFont.Bold)  # Slightly smaller font
                painter.setFont(font)
                
                # Set up text pen with orange color (40% opacity)
                text_pen = QPen(QColor(255, 140, 0, 102))  # Reduced opacity for text
                painter.setPen(text_pen)
                
                # Calculate middle Y position
                mid_y = self.height() // 2
                
                # Draw letters at the bottom and middle (aa-na)
                for i in range(self.grid_size):
                    x = i * self.cell_width
                    col_label = self.get_column_label(i)
                    text_x = x + (self.cell_width - painter.fontMetrics().horizontalAdvance(col_label)) // 2
                    
                    # Draw at bottom with semi-transparent background
                    self._draw_text_with_background(painter, text_x, self.height() - 15, col_label)
                    
                    # Draw in middle with semi-transparent background
                    self._draw_text_with_background(painter, text_x, mid_y, col_label)
                
                # Draw numbers on both sides (01-40)
                for i in range(self.grid_size):
                    y = i * self.cell_height
                    row_num = f"{i + 1:02d}"
                    text_y = y + (self.cell_height + painter.fontMetrics().height()) // 2
                    
                    # Left side numbers with semi-transparent background
                    self._draw_text_with_background(painter, 5, text_y, row_num)
                    
                    # Right side numbers with semi-transparent background
                    text_width = painter.fontMetrics().horizontalAdvance(row_num)
                    self._draw_text_with_background(painter, self.width() - text_width - 5, text_y, row_num)
                
                # Draw hover effect and coordinate display if mouse is over the grid
                if self.current_mouse_pos:
                    local_pos = self.mapFromGlobal(self.current_mouse_pos)
                    col = local_pos.x() // self.cell_width
                    row = local_pos.y() // self.cell_height
                    
                    if 0 <= col < self.grid_size and 0 <= row < self.grid_size:
                        # Get coordinate in aa01 format
                        col_label = self.get_column_label(col)
                        row_num = f"{row + 1:02d}"
                        coord_text = f"{col_label}{row_num}"
                        
                        # Highlight current cell with very light fill
                        cell_x = col * self.cell_width
                        cell_y = row * self.cell_height
                        painter.fillRect(cell_x, cell_y, self.cell_width, self.cell_height, 
                                      QColor(255, 140, 0, 32))  # Very light orange fill
                        
                        # Draw coordinate near cursor with enhanced visibility
                        self._draw_text_with_background(painter, 
                                                      local_pos.x() + 15,
                                                      local_pos.y() - 15,
                                                      coord_text,
                                                      enhanced=True)
            finally:
                painter.end()
        except Exception as e:
            logging.exception("Error in paintEvent: %s", e)

    def _draw_text_with_background(self, painter, x, y, text, enhanced=False):
        """Helper method to draw text with a semi-transparent background."""
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()
        
        # Create background rectangle
        margin = 3
        bg_rect = QRect(x - margin, y - text_height + margin,
                       text_width + 2 * margin, text_height + margin)
        
        # Draw semi-transparent background
        if enhanced:
            # More visible background for hover text
            painter.fillRect(bg_rect, QColor(0, 0, 0, 160))
            painter.setPen(QPen(QColor(255, 140, 0, 255)))  # Full opacity for hover text
        else:
            # Regular semi-transparent background
            painter.fillRect(bg_rect, QColor(0, 0, 0, 80))
            painter.setPen(QPen(QColor(255, 140, 0, 102)))  # 40% opacity for regular text
        
        # Draw text
        painter.drawText(x, y, text)

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
        
        # Create the grid overlay window
        self.grid_overlay = GridOverlayWindow()
        self.grid_overlay.hide()  # Hide by default
        
        self.initUI()
        self.execute_timer = QTimer(self)
        self.execute_timer.setSingleShot(True)
        self.execute_timer.timeout.connect(self._execute_action)
        screen_geom = QApplication.primaryScreen().geometry()
        if screen_geom:
            self.move(20, 20)
        self.setMinimumSize(600, 400)
        self.show()
        logging.info("AIControlWindow initialized.")
        self.show_message_signal.connect(self._show_message_on_main_thread)

    def closeEvent(self, event):
        """Handle cleanup when the window is closed"""
        try:
            # Stop all timers
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
            if hasattr(self, 'execute_timer'):
                self.execute_timer.stop()
            if hasattr(self, 'countdown_timer'):
                self.countdown_timer.stop()
                
            # Clean up worker thread if it exists
            if hasattr(self, 'worker') and self.worker is not None:
                if self.worker.isRunning():
                    self.worker.terminate()
                    self.worker.wait()  # Wait for thread to finish
                self.worker = None
                
            # Close grid overlay
            if self.grid_overlay:
                self.grid_overlay.close()
                
            # Clean up any remaining QApplication events
            QApplication.processEvents()
            
        except Exception as e:
            logging.exception("Error during window cleanup: %s", e)
            
        event.accept()

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
        instruction = QLabel("Enter what you want the AI to do:")
        instruction.setWordWrap(True)
        instruction.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(instruction)

        # Create horizontal layout for toggle button and click testing
        top_layout = QHBoxLayout()
        
        # Add grid toggle button
        self.grid_toggle = QPushButton("Show Grid")
        self.grid_toggle.setCheckable(True)  # Make it a toggle button
        self.grid_toggle.setChecked(False)  # Unchecked by default
        self.grid_toggle.clicked.connect(self.toggle_grid)
        self.grid_toggle.setStyleSheet("""
            QPushButton { padding: 5px 10px; }
            QPushButton:checked { background-color: #00aa00; }
        """)
        top_layout.addWidget(self.grid_toggle)

        # Add click testing section
        click_test_layout = QHBoxLayout()
        click_test_layout.setSpacing(5)
        
        # Add coordinate input for click testing
        self.coord_input = QLineEdit()
        self.coord_input.setPlaceholderText("Enter coordinate (aa01-na40)")
        self.coord_input.setMaximumWidth(200)
        self.coord_input.returnPressed.connect(self.execute_click)
        click_test_layout.addWidget(self.coord_input)
        
        # Add execute click button
        execute_click_btn = QPushButton("Test Click")
        execute_click_btn.clicked.connect(self.execute_click)
        click_test_layout.addWidget(execute_click_btn)
        
        top_layout.addLayout(click_test_layout)
        
        # Add stretch to push everything to the left
        top_layout.addStretch()
        
        # Add the top layout to main layout
        layout.addLayout(top_layout)

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
            QPushButton:checked { background-color: #00aa00; }
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

    def toggle_grid(self):
        """Toggle the grid overlay visibility"""
        if self.grid_toggle.isChecked():
            self.grid_overlay.show()
            self.grid_toggle.setText("Hide Grid")
        else:
            self.grid_overlay.hide()
            self.grid_toggle.setText("Show Grid")

    def execute_click(self):
        """Execute a click at the specified coordinate."""
        if QThread.currentThread() != QApplication.instance().thread():
            QMetaObject.invokeMethod(self, "execute_click", Qt.QueuedConnection)
            return
            
        coordinate = self.coord_input.text().strip().lower()
        if not coordinate:
            self.status_display.append("⚠️ Please enter a coordinate")
            return
            
        try:
            # Validate coordinate format
            if not self.controller.screen_mapper._validate_coordinate_format(coordinate):
                self.status_display.append(f"❌ Invalid coordinate format: {coordinate}. Use format aa01-na40")
                return
                
            # Execute the click
            success = self.controller.screen_mapper.execute_command(coordinate)
            
            if success:
                self.status_display.append(f"✓ Successfully clicked at coordinate {coordinate}")
                self.coord_input.clear()  # Clear input for next coordinate
            else:
                self.status_display.append(f"❌ Failed to click at coordinate {coordinate}")
                
        except Exception as e:
            error_msg = str(e)
            self.status_display.append(f"❌ Error: {error_msg}")
            logging.exception("Click execution error")

# End of AIControlWindow module.