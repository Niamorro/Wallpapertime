import configparser
import ctypes
import os
import subprocess
import sys
from datetime import datetime

from PySide6.QtCore import QTimer, Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QSystemTrayIcon,
    QMenu,
    QFileDialog,
    QMessageBox,
)

import qdarktheme
from screeninfo import get_monitors

class CheckboxUpdateThread(QThread):
    checkbox_states_updated = Signal()

    def run(self):
        while not self.isInterruptionRequested():
            self.msleep(1000)
            self.checkbox_states_updated.emit()

class WallpaperTimeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WallpaperTime")
        self.setWindowIcon(QIcon("icon.png"))
        self.setGeometry(100, 100, 1280, 720)

        # Change the current working directory
        os.chdir(os.path.dirname(sys.argv[0]))

        self.checkboxes = []

        # Tray setup
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        self.tray_menu = QMenu(self)
        self.tray_action_show = self.tray_menu.addAction("Show")
        self.tray_action_exit = self.tray_menu.addAction("Exit")
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # Load settings from file
        self.config = configparser.ConfigParser()

        self.autostart_checkbox = QCheckBox("Autostart", self)
        self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
        self.checkboxes.append(self.autostart_checkbox)

        self.start_minimized_checkbox = QCheckBox("Start Minimized", self)
        self.start_minimized_checkbox.stateChanged.connect(self.toggle_start_minimized)
        self.checkboxes.append(self.start_minimized_checkbox)

        self.load_settings()

        # Check if start_minimized is enabled and set window state accordingly
        if self.start_minimized_checkbox.isChecked():
            self.setWindowState(Qt.WindowMinimized)

        # Start the checkbox update thread
        self.checkbox_update_thread = CheckboxUpdateThread(self)
        self.checkbox_update_thread.checkbox_states_updated.connect(self.load_settings)
        self.checkbox_update_thread.start()

        # Tray icon click event
        self.tray_icon.activated.connect(self.handle_tray_icon_activated)

        # Timer to update wallpaper
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wallpaper)

        # Initialize intervals
        self.intervals = []
        self.load_intervals()

        # UI setup
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.interval_table = QTableWidget(self)
        self.interval_table.setColumnCount(3)
        self.interval_table.setHorizontalHeaderLabels(
            ["Start Time", "End Time", "Wallpaper Path"]
        )
        self.interval_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.interval_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.update_interval_table()

        self.start_time_input = QLineEdit(self)
        self.end_time_input = QLineEdit(self)
        self.wallpaper_path_input = QLineEdit(self)
        self.wallpaper_path_button = QPushButton("Select Wallpaper", self)
        self.wallpaper_path_button.clicked.connect(self.select_wallpaper)

        self.add_button = QPushButton("Add", self)
        self.add_button.clicked.connect(self.add_interval)

        self.edit_button = QPushButton("Edit", self)
        self.edit_button.clicked.connect(self.edit_interval)

        self.delete_button = QPushButton("Delete", self)
        self.delete_button.clicked.connect(self.delete_interval)

        self.minimize_button = QPushButton("Minimize", self)
        self.minimize_button.clicked.connect(self.handle_minimize_button_clicked)
        self.minimize_button.setEnabled(True)

        # Status label for visualization
        self.status_label = QLabel(self)
        self.status_label.setAlignment(Qt.AlignCenter)

        # Rename the method to avoid conflict
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.addWidget(self.interval_table)

        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Start Time:"))
        form_layout.addWidget(self.start_time_input)
        form_layout.addWidget(QLabel("End Time:"))
        form_layout.addWidget(self.end_time_input)
        form_layout.addWidget(QLabel("Wallpaper Path:"))
        form_layout.addWidget(self.wallpaper_path_input)
        form_layout.addWidget(self.wallpaper_path_button)

        self.main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.autostart_checkbox)
        button_layout.addWidget(self.start_minimized_checkbox)
        button_layout.addWidget(self.minimize_button)

        self.main_layout.addLayout(button_layout)
        self.main_layout.addWidget(self.status_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wallpaper)
        self.timer.start(1000)

        # Set the style sheet
        qdarktheme.setup_theme("auto")
        
        self.show()

    def update_checkbox_states(self):
        for checkbox in self.checkboxes:
            checkbox_name = checkbox.text().replace(" ", "").lower()
            if self.config.has_option("General", checkbox_name):
                checkbox_state = self.config.getboolean("General", checkbox_name)
                checkbox.setChecked(checkbox_state)

    def update_interval_table(self):
        self.interval_table.clearContents()
        self.interval_table.setRowCount(0)
        for i, (start_time, end_time, wallpaper_path) in enumerate(self.intervals):
            self.interval_table.insertRow(i)
            self.interval_table.setItem(i, 0, QTableWidgetItem(start_time))
            self.interval_table.setItem(i, 1, QTableWidgetItem(end_time))
            self.interval_table.setItem(i, 2, QTableWidgetItem(wallpaper_path))

    def load_settings(self):
        config = configparser.ConfigParser()
        config.read("settings.ini")

        if config.has_section("Intervals"):
            self.intervals = []
            for key, value in config.items("Intervals"):
                start_time, end_time, wallpaper_path = value.split(",")
                self.intervals.append((start_time, end_time, wallpaper_path))

        if config.has_section("General"):
            for checkbox in self.checkboxes:
                checkbox_name = checkbox.text().replace(" ", "").lower()
                if config.has_option("General", checkbox_name):
                    checkbox_state = config.getboolean("General", checkbox_name)
                    checkbox.setChecked(checkbox_state)
                    checkbox.update()  # Update the checkbox display

            # Check if start_minimized is enabled and set checkbox state accordingly
            if config.has_option("General", "startminimized"):
                start_minimized = config.getboolean("General", "startminimized")
                self.start_minimized_checkbox.setChecked(start_minimized)

        self.update_checkbox_states()

    def toggle_start_minimized(self):
        start_minimized = self.start_minimized_checkbox.isChecked()
        self.setWindowState(Qt.WindowMinimized if start_minimized else Qt.WindowNoState)
        self.save_settings()   # Move the save_settings() call here

    def save_settings(self):
        config = configparser.ConfigParser()

        if not config.has_section("Intervals"):
            config.add_section("Intervals")
        for i, (start_time, end_time, wallpaper_path) in enumerate(self.intervals):
            config.set(
                "Intervals", f"interval{i}", f"{start_time},{end_time},{wallpaper_path}"
            )

        if not config.has_section("General"):
            config.add_section("General")
        for checkbox in self.checkboxes:
            checkbox_name = checkbox.text().replace(" ", "").lower()
            config.set("General", checkbox_name, str(checkbox.isChecked()))

        # Save the start_minimized state
        config.set("General", "startminimized", str(self.start_minimized_checkbox.isChecked()))

        with open("settings.ini", "w") as config_file:
            config.write(config_file)

    def load_intervals(self):
        config = configparser.ConfigParser()
        config.read("settings.ini")

        if config.has_section("Intervals"):
            self.intervals = []
            for key in config["Intervals"]:
                start_time, end_time, wallpaper_path = config["Intervals"][key].split(
                    ","
                )
                self.intervals.append((start_time, end_time, wallpaper_path))

    def handle_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()  # Use showNormal() to restore the window
            self.tray_icon.hide()

    def handle_minimize_button_clicked(self):
        self.hide()
        self.tray_icon.show()

    def add_interval(self):
        start_time = self.start_time_input.text()
        end_time = self.end_time_input.text()
        wallpaper_path = self.wallpaper_path_input.text()

        if not start_time or not end_time or not wallpaper_path:
            QMessageBox.critical(
                self, "Error", "Please fill in all fields before adding an interval."
            )
            return

        if not self.validate_time_format(start_time) or not self.validate_time_format(
            end_time
        ):
            QMessageBox.critical(
                self, "Error", "Invalid time format. Please use HH:MM format."
            )
            return

        self.intervals.append((start_time, end_time, wallpaper_path))
        self.update_interval_table()
        self.save_settings()

    def validate_time_format(self, time_str):
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            return False

    def edit_interval(self):
        selected_row = self.interval_table.currentRow()
        if selected_row != -1:
            start_time = self.start_time_input.text()
            end_time = self.end_time_input.text()
            wallpaper_path = self.wallpaper_path_input.text()

            if not start_time or not end_time or not wallpaper_path:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Please fill in all fields before editing the interval.",
                )
                return

            if not self.validate_time_format(
                start_time
            ) or not self.validate_time_format(end_time):
                QMessageBox.critical(
                    self, "Error", "Invalid time format. Please use HH:MM format."
                )
                return

            self.intervals[selected_row] = (start_time, end_time, wallpaper_path)
            self.update_interval_table()
            self.save_settings()

    def delete_interval(self):
        selected_row = self.interval_table.currentRow()
        if selected_row != -1:
            del self.intervals[selected_row]
            self.update_interval_table()
            self.save_settings()

    def create_autostart_entry(self):
        script_path = os.path.abspath(sys.argv[0])
        key_path = r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"
        key_name = "WallpaperTime"
        value = f'"{script_path}"'

        try:
            subprocess.run(
            ["reg", "add", key_path, "/v", key_name, "/d", value, "/f"], check=True
            )
        except subprocess.CalledProcessError as e:
            print("Error creating autostart entry:", e)

    def remove_autostart_entry(self):
        key_path = r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"
        key_name = "WallpaperTime"

        try:
            subprocess.run(
                ["reg", "delete", key_path, "/v", key_name, "/f"], check=True
            )
        except subprocess.CalledProcessError as e:
            print("Error removing autostart entry:", e)

    def toggle_autostart(self):
        autostart_enabled = self.autostart_checkbox.isChecked()
        if autostart_enabled:
            self.create_autostart_entry()
            if self.start_minimized_checkbox.isChecked():
                self.handle_minimize_button_clicked()
        else:
            self.remove_autostart_entry()
        self.save_settings()


    def is_between_times(self, current_time, start_time, end_time):
        current_time = datetime.now().time()

        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            return start_time <= current_time or current_time <= end_time


    def update_wallpaper(self):
        current_time = datetime.now().time()
        wallpaper_path = None

        for start_time, end_time, path in self.intervals:
            start_time = datetime.strptime(start_time, "%H:%M").time()
            end_time = datetime.strptime(end_time, "%H:%M").time()

            if self.is_between_times(str(current_time), start_time, end_time):
                wallpaper_path = path
                print(f"Interval matched: {start_time} - {end_time}")
                break
            else:
                print(f"No match for interval: {start_time} - {end_time}, current time: {current_time}")

        if wallpaper_path:
            try:
                self.set_wallpaper(wallpaper_path)
                self.status_label.setText(f"Wallpaper updated at {datetime.now().strftime('%H:%M:%S')}")
            except Exception as e:
                self.status_label.setText(f"Error updating wallpaper: {e}")
        else:
            print(f"No wallpaper set for the current time: {current_time}")
            self.status_label.setText("No wallpaper set for the current time.")

    def set_wallpaper(self, path):
        # Check if the file exists
        if not os.path.exists(path):
            self.status_label.setText(f"Error: The wallpaper file '{path}' does not exist.")
            return

        # Convert the wallpaper path to a format compatible with SystemParametersInfo function
        wallpaper_path = os.path.abspath(path)

        # Set the wallpaper for all monitors
        SPI_SETDESKWALLPAPER = 20
        for monitor in get_monitors():
            ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, wallpaper_path, 3
            )

    def select_wallpaper(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Wallpaper",
            "",
            "Images (*.jpg *.png *.jpeg);;All Files (*)",
            options=options,
        )
        if file_path:
            self.wallpaper_path_input.setText(file_path)

    def closeEvent(self, event):
        self.tray_icon.hide()
        self.timer.stop()
        self.save_settings()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme()
    os.chdir(os.path.dirname(sys.argv[0]))
    if not os.path.exists("icon.png"):
        print(
            "The icon.png file is missing. Please place it in the same directory as the script."
        )
        sys.exit(1)

    window = WallpaperTimeApp()
    sys.exit(app.exec())
