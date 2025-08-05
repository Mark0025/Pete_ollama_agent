"""
PeteOllama V1 - Main GUI Window
===============================

Beautiful PyQt5 interface for testing the AI property manager.
Allows testing conversations, viewing training data, and monitoring performance.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTextEdit, QLineEdit, QPushButton,
    QLabel, QGroupBox, QProgressBar, QTableWidget,
    QTableWidgetItem, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.model_manager import ModelManager
from database.pete_db_manager import PeteDBManager
from utils.logger import logger

class ModelTestThread(QThread):
    """Background thread for testing AI model responses"""
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model_manager, prompt):
        super().__init__()
        self.model_manager = model_manager
        self.prompt = prompt
    
    def run(self):
        try:
            response = self.model_manager.generate_response(self.prompt)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

class PeteOllamaGUI(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.model_manager = ModelManager()
        self.db_manager = PeteDBManager()
        self.init_ui()
        self.setup_connections()
        self.start_status_updates()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("PeteOllama V1 - AI Property Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create header
        self.create_header(main_layout)
        
        # Create tab widget
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Create tabs
        self.create_chat_tab(tab_widget)
        self.create_training_tab(tab_widget)
        self.create_monitoring_tab(tab_widget)
        self.create_settings_tab(tab_widget)
    
    def create_header(self, parent_layout):
        """Create application header"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2E7D32;
                border-radius: 8px;
                margin: 5px;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Title and subtitle
        title_layout = QVBoxLayout()
        title_label = QLabel("🏠 PeteOllama V1")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        subtitle_label = QLabel("AI Property Manager • Trained on Real Conversations")
        subtitle_label.setFont(QFont("Arial", 10))
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Status indicators
        self.model_status = QLabel("🤖 Model: Loading...")
        self.db_status = QLabel("🗄️  Database: Checking...")
        self.vapi_status = QLabel("🎤 VAPI: Disconnected")
        
        status_layout = QVBoxLayout()
        status_layout.addWidget(self.model_status)
        status_layout.addWidget(self.db_status)
        status_layout.addWidget(self.vapi_status)
        header_layout.addLayout(status_layout)
        
        parent_layout.addWidget(header_frame)
    
    def create_chat_tab(self, tab_widget):
        """Create chat testing tab"""
        chat_widget = QWidget()
        layout = QVBoxLayout(chat_widget)
        
        # Chat area
        chat_group = QGroupBox("💬 Test AI Conversations")
        chat_layout = QVBoxLayout(chat_group)
        
        # Conversation display
        self.conversation_display = QTextEdit()
        self.conversation_display.setMinimumHeight(300)
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setStyleSheet("""
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Courier New', monospace;
            }
        """)
        chat_layout.addWidget(self.conversation_display)
        
        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your property management question here...")
        self.message_input.setMinimumHeight(40)
        
        self.send_button = QPushButton("Send Message")
        self.send_button.setFixedWidth(120)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        chat_layout.addLayout(input_layout)
        
        layout.addWidget(chat_group)
        
        # Quick test buttons
        quick_test_group = QGroupBox("🚀 Quick Tests")
        quick_layout = QHBoxLayout(quick_test_group)
        
        test_buttons = [
            ("Rent Inquiry", "Hi, when is my rent due this month?"),
            ("Maintenance Request", "My kitchen faucet is leaking, can you help?"),
            ("Lease Question", "I want to renew my lease for another year"),
            ("Property Info", "What's the square footage of my apartment?")
        ]
        
        for button_text, test_prompt in test_buttons:
            btn = QPushButton(button_text)
            btn.clicked.connect(lambda checked, prompt=test_prompt: self.send_test_message(prompt))
            quick_layout.addWidget(btn)
        
        layout.addWidget(quick_test_group)
        
        tab_widget.addTab(chat_widget, "💬 Chat Test")
    
    def create_training_tab(self, tab_widget):
        """Create training data viewer tab"""
        training_widget = QWidget()
        layout = QVBoxLayout(training_widget)
        
        # Training data stats
        stats_group = QGroupBox("📊 Training Data Statistics")
        stats_layout = QHBoxLayout(stats_group)
        
        self.total_conversations_label = QLabel("Total Conversations: Loading...")
        self.avg_duration_label = QLabel("Avg Duration: Loading...")
        self.date_range_label = QLabel("Date Range: Loading...")
        
        stats_layout.addWidget(self.total_conversations_label)
        stats_layout.addWidget(self.avg_duration_label)
        stats_layout.addWidget(self.date_range_label)
        
        layout.addWidget(stats_group)
        
        # Sample conversations table
        conversations_group = QGroupBox("📞 Sample Conversations")
        conversations_layout = QVBoxLayout(conversations_group)
        
        self.conversations_table = QTableWidget()
        self.conversations_table.setColumnCount(4)
        self.conversations_table.setHorizontalHeaderLabels([
            "Date", "Duration", "Type", "Preview"
        ])
        self.conversations_table.horizontalHeader().setStretchLastSection(True)
        
        conversations_layout.addWidget(self.conversations_table)
        layout.addWidget(conversations_group)
        
        tab_widget.addTab(training_widget, "📚 Training Data")
    
    def create_monitoring_tab(self, tab_widget):
        """Create system monitoring tab"""
        monitoring_widget = QWidget()
        layout = QVBoxLayout(monitoring_widget)
        
        # Model performance
        perf_group = QGroupBox("🎯 Model Performance")
        perf_layout = QVBoxLayout(perf_group)
        
        self.response_time_label = QLabel("Avg Response Time: -- ms")
        self.accuracy_label = QLabel("Estimated Accuracy: --%")
        self.model_temp_label = QLabel("Model Temperature: 0.7")
        
        perf_layout.addWidget(self.response_time_label)
        perf_layout.addWidget(self.accuracy_label)
        perf_layout.addWidget(self.model_temp_label)
        
        layout.addWidget(perf_group)
        
        # System resources
        resources_group = QGroupBox("💾 System Resources")
        resources_layout = QVBoxLayout(resources_group)
        
        self.memory_usage = QProgressBar()
        self.memory_usage.setFormat("Memory Usage: %p%")
        
        self.cpu_usage = QProgressBar()
        self.cpu_usage.setFormat("CPU Usage: %p%")
        
        resources_layout.addWidget(QLabel("Memory Usage:"))
        resources_layout.addWidget(self.memory_usage)
        resources_layout.addWidget(QLabel("CPU Usage:"))
        resources_layout.addWidget(self.cpu_usage)
        
        layout.addWidget(resources_group)
        
        tab_widget.addTab(monitoring_widget, "📊 Monitoring")
    
    def create_settings_tab(self, tab_widget):
        """Create settings and configuration tab"""
        settings_widget = QWidget()
        layout = QVBoxLayout(settings_widget)
        
        # Model settings
        model_group = QGroupBox("🤖 Model Configuration")
        model_layout = QVBoxLayout(model_group)
        
        # Model controls
        model_controls = QHBoxLayout()
        
        self.download_model_btn = QPushButton("📥 Download Model")
        self.train_model_btn = QPushButton("🎓 Train Model")
        self.test_model_btn = QPushButton("🧪 Test Model")
        
        model_controls.addWidget(self.download_model_btn)
        model_controls.addWidget(self.train_model_btn)
        model_controls.addWidget(self.test_model_btn)
        model_controls.addStretch()
        
        model_layout.addLayout(model_controls)
        layout.addWidget(model_group)
        
        # Database settings
        db_group = QGroupBox("🗄️  Database Configuration")
        db_layout = QVBoxLayout(db_group)
        
        db_controls = QHBoxLayout()
        self.extract_data_btn = QPushButton("📊 Extract Training Data")
        self.view_db_btn = QPushButton("👁️  View Database")
        self.backup_db_btn = QPushButton("💾 Backup Database")
        
        db_controls.addWidget(self.extract_data_btn)
        db_controls.addWidget(self.view_db_btn)
        db_controls.addWidget(self.backup_db_btn)
        db_controls.addStretch()
        
        db_layout.addLayout(db_controls)
        layout.addWidget(db_group)
        
        # VAPI settings
        vapi_group = QGroupBox("🎤 VAPI Configuration")
        vapi_layout = QVBoxLayout(vapi_group)
        
        vapi_controls = QHBoxLayout()
        self.connect_vapi_btn = QPushButton("🔗 Connect VAPI")
        self.test_webhook_btn = QPushButton("🌐 Test Webhook")
        self.view_calls_btn = QPushButton("📞 View Call Logs")
        
        vapi_controls.addWidget(self.connect_vapi_btn)
        vapi_controls.addWidget(self.test_webhook_btn)
        vapi_controls.addWidget(self.view_calls_btn)
        vapi_controls.addStretch()
        
        vapi_layout.addLayout(vapi_controls)
        layout.addWidget(vapi_group)
        
        layout.addStretch()
        tab_widget.addTab(settings_widget, "⚙️ Settings")
    
    def setup_connections(self):
        """Setup signal/slot connections"""
        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)
        
        # Settings tab connections
        self.extract_data_btn.clicked.connect(self.extract_training_data)
        self.download_model_btn.clicked.connect(self.download_model)
        self.train_model_btn.clicked.connect(self.train_model)
    
    def start_status_updates(self):
        """Start periodic status updates"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
        # Initial update
        self.update_status()
        self.load_training_data_stats()
    
    def update_status(self):
        """Update status indicators"""
        # Check model status
        if self.model_manager.is_available():
            self.model_status.setText("🤖 Model: Ready")
            self.model_status.setStyleSheet("color: #4CAF50;")
        else:
            self.model_status.setText("🤖 Model: Loading...")
            self.model_status.setStyleSheet("color: #FF9800;")
        
        # Check database status
        if self.db_manager.is_connected():
            self.db_status.setText("🗄️  Database: Connected")
            self.db_status.setStyleSheet("color: #4CAF50;")
        else:
            self.db_status.setText("🗄️  Database: Disconnected")
            self.db_status.setStyleSheet("color: #F44336;")
    
    def send_message(self):
        """Send message to AI model"""
        message = self.message_input.text().strip()
        if not message:
            return
        
        # Display user message
        self.conversation_display.append(f"<div style='color: #2196F3; font-weight: bold;'>You:</div>")
        self.conversation_display.append(f"<div style='margin-bottom: 10px;'>{message}</div>")
        
        # Clear input
        self.message_input.clear()
        
        # Send to model (in background thread)
        self.send_button.setEnabled(False)
        self.send_button.setText("Thinking...")
        
        self.model_thread = ModelTestThread(self.model_manager, message)
        self.model_thread.response_ready.connect(self.on_response_ready)
        self.model_thread.error_occurred.connect(self.on_response_error)
        self.model_thread.start()
    
    def send_test_message(self, prompt):
        """Send a predefined test message"""
        self.message_input.setText(prompt)
        self.send_message()
    
    def on_response_ready(self, response):
        """Handle AI model response"""
        self.conversation_display.append(f"<div style='color: #4CAF50; font-weight: bold;'>PeteOllama:</div>")
        self.conversation_display.append(f"<div style='margin-bottom: 15px; padding: 10px; background-color: #f0f8f0; border-left: 3px solid #4CAF50;'>{response}</div>")
        
        # Re-enable button
        self.send_button.setEnabled(True)
        self.send_button.setText("Send Message")
        
        # Scroll to bottom
        scrollbar = self.conversation_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_response_error(self, error):
        """Handle AI model error"""
        self.conversation_display.append(f"<div style='color: #F44336; font-weight: bold;'>Error:</div>")
        self.conversation_display.append(f"<div style='margin-bottom: 15px; color: #F44336;'>{error}</div>")
        
        # Re-enable button
        self.send_button.setEnabled(True)
        self.send_button.setText("Send Message")
    
    def load_training_data_stats(self):
        """Load training data statistics"""
        try:
            stats = self.db_manager.get_training_stats()
            if stats:
                self.total_conversations_label.setText(f"Total Conversations: {stats['total']}")
                self.avg_duration_label.setText(f"Avg Duration: {stats['avg_duration']}s")
                self.date_range_label.setText(f"Date Range: {stats['date_range']}")
                
                # Load sample conversations
                self.load_sample_conversations()
        except Exception as e:
            logger.error(f"Failed to load training stats: {e}")
    
    def load_sample_conversations(self):
        """Load sample conversations into table"""
        try:
            conversations = self.db_manager.get_sample_conversations(limit=20)
            
            self.conversations_table.setRowCount(len(conversations))
            for row, conv in enumerate(conversations):
                self.conversations_table.setItem(row, 0, QTableWidgetItem(conv['date']))
                self.conversations_table.setItem(row, 1, QTableWidgetItem(f"{conv['duration']}s"))
                self.conversations_table.setItem(row, 2, QTableWidgetItem(conv['type']))
                self.conversations_table.setItem(row, 3, QTableWidgetItem(conv['preview']))
        
        except Exception as e:
            logger.error(f"Failed to load sample conversations: {e}")
    
    def extract_training_data(self):
        """Extract training data from production database"""
        self.extract_data_btn.setEnabled(False)
        self.extract_data_btn.setText("Extracting...")
        
        # TODO: Implement data extraction
        logger.info("Training data extraction requested")
        
        # Re-enable after delay (simulate work)
        QTimer.singleShot(3000, lambda: [
            self.extract_data_btn.setEnabled(True),
            self.extract_data_btn.setText("📊 Extract Training Data")
        ])
    
    def download_model(self):
        """Download the base AI model"""
        self.download_model_btn.setEnabled(False)
        self.download_model_btn.setText("Downloading...")
        
        # TODO: Implement model download
        logger.info("Model download requested")
    
    def train_model(self):
        """Train the AI model on phone conversation data"""
        self.train_model_btn.setEnabled(False)
        self.train_model_btn.setText("Training...")
        
        # TODO: Implement model training
        logger.info("Model training requested")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = PeteOllamaGUI()
    window.show()
    sys.exit(app.exec_())