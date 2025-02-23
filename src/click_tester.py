#!/usr/bin/env python3

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLineEdit, QPushButton, QLabel)
from PySide6.QtCore import Qt, QThread, QMetaObject
from screen_mapper import ScreenMapper

class ClickTesterWindow(QMainWindow):
    """Simple window for testing grid coordinate clicks."""
    
    def __init__(self):
        super().__init__()
        # Create ScreenMapper in the main thread
        if QThread.currentThread() != QApplication.instance().thread():
            raise RuntimeError("ClickTesterWindow must be created in the main thread")
        self.screen_mapper = ScreenMapper()
        self.initUI()
        
    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("Grid Click Tester")
        self.setMinimumSize(400, 200)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # Keep window on top
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Add instruction label
        instruction_label = QLabel("Enter a grid coordinate (e.g., aa01) and click 'Execute' or press Enter")
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)
        
        # Create input layout
        input_layout = QHBoxLayout()
        
        # Add coordinate input
        self.coord_input = QLineEdit()
        self.coord_input.setPlaceholderText("Enter coordinate (aa01-na40)")
        self.coord_input.returnPressed.connect(self.execute_click)
        input_layout.addWidget(self.coord_input)
        
        # Add execute button
        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self.execute_click)
        input_layout.addWidget(execute_btn)
        
        layout.addLayout(input_layout)
        
        # Add status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Style the window
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QWidget { background-color: #2b2b2b; color: #ffffff; }
            QLabel { font-size: 13px; padding: 5px; }
            QLineEdit { 
                padding: 8px; 
                border: 1px solid #555555; 
                border-radius: 3px; 
                background-color: #363636; 
                font-size: 14px; 
                color: white;
            }
            QPushButton { 
                padding: 8px 15px; 
                background-color: #0066cc; 
                border: none; 
                border-radius: 3px; 
                color: white;
                font-size: 14px; 
            }
            QPushButton:hover { background-color: #0077ee; }
        """)
        
    def execute_click(self):
        """Execute the click at the specified coordinate."""
        if QThread.currentThread() != QApplication.instance().thread():
            QMetaObject.invokeMethod(self, "execute_click", Qt.QueuedConnection)
            return
            
        coordinate = self.coord_input.text().strip().lower()
        if not coordinate:
            self.status_label.setText("Please enter a coordinate")
            self.status_label.setStyleSheet("color: yellow")
            return
            
        try:
            # Validate coordinate format
            if not self.screen_mapper._validate_coordinate_format(coordinate):
                self.status_label.setText(f"Invalid coordinate format: {coordinate}. Use format aa01-na40")
                self.status_label.setStyleSheet("color: red")
                return
                
            # Execute the click
            success = self.screen_mapper.execute_command(coordinate)
            
            if success:
                self.status_label.setText(f"Successfully clicked at coordinate {coordinate}")
                self.status_label.setStyleSheet("color: #00ff00")  # Bright green
                self.coord_input.clear()  # Clear input for next coordinate
            else:
                self.status_label.setText(f"Failed to click at coordinate {coordinate}")
                self.status_label.setStyleSheet("color: red")
                
        except Exception as e:
            error_msg = str(e)
            self.status_label.setText(f"Error: {error_msg}")
            self.status_label.setStyleSheet("color: red")
            logging.exception("Click execution error")

def main():
    """Main entry point for the click tester application."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    try:
        window = ClickTesterWindow()
        window.show()
        return app.exec()
    except Exception as e:
        logging.exception("Application error: %s", e)
        return 1

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main()) 