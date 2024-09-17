import sys
import re
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QLineEdit, QDialog,
    QFormLayout, QHeaderView
)
from PyQt5.QtCore import Qt

class OilChangeLogApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oil Change Log Parser")
        self.resize(800, 600)

        self.file_path = ''
        self.vehicle_info = ''
        self.oil_changes = []
        self.current_estimated_mileage = 'NA'
        self.default_oil_type = ''
        self.default_filter_type = ''
        self.last_date_from_log = ''
        self.last_oil_change_mileage = '0'

        self.init_ui()

    def init_ui(self):
        # Vehicle Information Label
        self.vehicle_info_label = QLabel("Vehicle: Not specified")
        self.vehicle_info_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # File Selection Layout
        file_layout = QHBoxLayout()
        file_label = QLabel("Selected File:")
        self.file_name_label = QLabel("No file selected")
        select_file_button = QPushButton("Select File")
        select_file_button.clicked.connect(self.select_file)

        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_name_label)
        file_layout.addWidget(select_file_button)

        # Add New Entry Button
        add_entry_button = QPushButton("Add New Oil Change Entry")
        add_entry_button.clicked.connect(self.add_new_entry)

        # Table Widget to Display Oil Changes
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(['Mileage', 'Date', 'Oil Type', 'Filter Type'])
        self.table_widget.horizontalHeader().setStretchLastSection(True)

        # Adjust the Date column width to fit the data
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        # Estimated Mileage Label
        self.estimated_mileage_label = QLabel("Estimated Current Mileage: NA")

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.vehicle_info_label)
        main_layout.addLayout(file_layout)
        main_layout.addWidget(self.table_widget)
        main_layout.addWidget(add_entry_button)
        main_layout.addWidget(self.estimated_mileage_label)

        self.setLayout(main_layout)

    def select_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Maintenance Log File", "",
                                                   "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            self.file_path = file_path
            self.file_name_label.setText(os.path.basename(self.file_path))
            self.parse_and_display()  # Automatically parse and display data

    def parse_and_display(self):
        if not self.file_path:
            QMessageBox.warning(self, "No File Selected", "Please select a maintenance log file.")
            return

        self.parse_oil_changes()
        self.display_oil_changes()
        self.calculate_estimated_mileage()

    def parse_oil_changes(self):
        # Initialize variables
        self.oil_changes = []
        self.vehicle_info = ''
        current_date = 'NA'

        # Regular expressions
        date_pattern = re.compile(r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$')
        mileage_pattern = re.compile(r'^(\d+)\s*miles\s*:\s*(.*)$', re.IGNORECASE)
        oil_change_pattern = re.compile(r'oil\s*and\s*filter\s*change', re.IGNORECASE)
        oil_type_pattern = re.compile(r'\((\dW-\d+)\)', re.IGNORECASE)
        filter_type_pattern = re.compile(r'\(([^()]*?[A-Z]+\d+[^()]*)\)', re.IGNORECASE)

        try:
            with open(self.file_path, 'r') as file:
                lines = file.readlines()
                i = 0

                # Read the vehicle information from the first non-empty line
                while i < len(lines):
                    line = lines[i].strip()
                    if line:
                        self.vehicle_info = line
                        break
                    i += 1

                i += 1  # Move to the next line after vehicle info

                while i < len(lines):
                    line = lines[i].strip()
                    # Skip empty lines
                    if not line:
                        i += 1
                        continue
                    # Check if the line is a date
                    if date_pattern.match(line):
                        current_date = line
                        i += 1
                        continue
                    # Check if the line contains mileage information
                    mileage_match = mileage_pattern.match(line)
                    if mileage_match:
                        mileage = mileage_match.group(1)
                        description = mileage_match.group(2)

                        # Combine with next line if necessary
                        full_description = description
                        if (i + 1) < len(lines):
                            next_line = lines[i + 1].strip()
                            if not date_pattern.match(next_line) and not mileage_pattern.match(next_line):
                                full_description += ' ' + next_line
                                i += 1  # Skip next line

                        # Check for oil change
                        if oil_change_pattern.search(full_description):
                            # Extract oil type
                            oil_type_match = oil_type_pattern.search(full_description)
                            oil_type = oil_type_match.group(1) if oil_type_match else 'NA'

                            # Extract filter type
                            parentheses_contents = re.findall(r'\(([^()]+)\)', full_description)
                            filter_type = 'NA'
                            for content in parentheses_contents:
                                if content.strip().lower() == oil_type.lower():
                                    continue
                                if re.match(r'[A-Z]+[\dA-Z]+', content.strip()):
                                    filter_type = content.strip()
                                    break

                            # Append to oil_changes list
                            self.oil_changes.append({
                                'Mileage': mileage,
                                'Date': current_date,
                                'Oil Type': oil_type,
                                'Filter Type': filter_type
                            })
                    i += 1

            # Update default oil and filter types and last date/mileage
            if self.oil_changes:
                last_entry = self.oil_changes[-1]
                self.default_oil_type = last_entry.get('Oil Type', '')
                self.default_filter_type = last_entry.get('Filter Type', '')
                self.last_date_from_log = last_entry.get('Date', '')
                self.last_oil_change_mileage = last_entry.get('Mileage', '0')
            else:
                self.default_oil_type = ''
                self.default_filter_type = ''
                self.last_date_from_log = ''
                self.last_oil_change_mileage = '0'

            # Update vehicle info label
            if self.vehicle_info:
                self.vehicle_info_label.setText(f"Vehicle: {self.vehicle_info}")
            else:
                self.vehicle_info_label.setText("Vehicle: Not specified")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read file: {e}")

    def display_oil_changes(self):
        self.table_widget.setRowCount(0)  # Clear existing rows

        if not self.oil_changes:
            QMessageBox.information(self, "No Oil Changes Found", "No oil changes found in the selected file.")
            return

        self.table_widget.setRowCount(len(self.oil_changes))
        for row_idx, entry in enumerate(self.oil_changes):
            self.table_widget.setItem(row_idx, 0, QTableWidgetItem(entry['Mileage']))
            self.table_widget.setItem(row_idx, 1, QTableWidgetItem(entry['Date']))
            self.table_widget.setItem(row_idx, 2, QTableWidgetItem(entry['Oil Type']))
            self.table_widget.setItem(row_idx, 3, QTableWidgetItem(entry['Filter Type']))

    def add_new_entry(self):
        self.new_entry_dialog = AddEntryDialog(self)
        self.new_entry_dialog.exec_()

    def refresh_display(self):
        self.parse_and_display()

    def calculate_estimated_mileage(self):
        # Calculate average mileage per day and estimate current mileage
        if len(self.oil_changes) < 2:
            self.current_estimated_mileage = 'NA'
            self.estimated_mileage_label.setText("Estimated Current Mileage: NA")
            return

        # Collect dates and mileages
        dates = []
        mileages = []

        for entry in self.oil_changes:
            date_str = entry['Date']
            mileage = int(entry['Mileage'])
            # Parse the date
            try:
                date = datetime.strptime(date_str, '%B %Y')
            except ValueError:
                continue  # Skip entries with invalid dates
            dates.append(date)
            mileages.append(mileage)

        if len(dates) < 2:
            self.current_estimated_mileage = 'NA'
            self.estimated_mileage_label.setText("Estimated Current Mileage: NA")
            return

        # Sort the entries by date
        sorted_entries = sorted(zip(dates, mileages), key=lambda x: x[0])

        # Calculate total days and total mileage difference
        total_days = (sorted_entries[-1][0] - sorted_entries[0][0]).days
        total_mileage = sorted_entries[-1][1] - sorted_entries[0][1]

        if total_days <= 0:
            self.current_estimated_mileage = 'NA'
            self.estimated_mileage_label.setText("Estimated Current Mileage: NA")
            return

        # Average mileage per day
        avg_mileage_per_day = total_mileage / total_days

        # Calculate days since last entry
        last_date = sorted_entries[-1][0]
        last_mileage = sorted_entries[-1][1]
        today = datetime.today()
        days_since_last = (today - last_date).days

        # Estimated current mileage
        estimated_current_mileage = int(last_mileage + (avg_mileage_per_day * days_since_last))

        self.current_estimated_mileage = estimated_current_mileage
        self.estimated_mileage_label.setText(f"Estimated Current Mileage: {estimated_current_mileage}")

class AddEntryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Oil Change Entry")
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.mileage_edit = QLineEdit()
        self.date_edit = QLineEdit()

        # Set the date to the last date from the log and make it read-only
        last_date = self.parent.last_date_from_log
        self.date_edit.setText(last_date)
        self.date_edit.setReadOnly(True)

        # Auto-populate the mileage with estimated current mileage
        estimated_mileage = self.parent.current_estimated_mileage
        if estimated_mileage != 'NA':
            self.mileage_edit.setText(str(estimated_mileage))

        # Auto-populate oil type and filter type with last used values
        self.oil_type_edit = QLineEdit()
        self.filter_type_edit = QLineEdit()
        self.oil_type_edit.setText(self.parent.default_oil_type)
        self.filter_type_edit.setText(self.parent.default_filter_type)

        form_layout = QFormLayout()
        form_layout.addRow("Mileage:", self.mileage_edit)
        form_layout.addRow("Date (Read-Only):", self.date_edit)
        form_layout.addRow("Oil Type (e.g., 5W-20):", self.oil_type_edit)
        form_layout.addRow("Filter Type (e.g., XG9688):", self.filter_type_edit)

        save_button = QPushButton("Save Entry")
        save_button.clicked.connect(self.save_entry)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(save_button)

        self.setLayout(main_layout)

    def save_entry(self):
        mileage = self.mileage_edit.text().strip()
        date = self.date_edit.text().strip()
        oil_type = self.oil_type_edit.text().strip()
        filter_type = self.filter_type_edit.text().strip()

        # Validate inputs
        if not mileage.isdigit():
            QMessageBox.warning(self, "Invalid Input", "Mileage must be a number.")
            return

        # Ensure mileage is not lower than the previous oil change mileage
        last_mileage = int(self.parent.last_oil_change_mileage)
        if int(mileage) < last_mileage:
            QMessageBox.warning(self, "Invalid Input", "Mileage cannot be lower than the previous oil change mileage.")
            return

        # Format the new entry
        new_entry_lines = []
        # Since we're always using the existing date, we don't need to add a new date heading
        new_entry_lines.append(f"{mileage} miles : Oil and Filter change ({oil_type}) ({filter_type})\n")

        # Append the new entry to the file
        try:
            with open(self.parent.file_path, 'a') as file:
                file.writelines(new_entry_lines)
            QMessageBox.information(self, "Success", "New oil change entry added successfully.")
            self.parent.refresh_display()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to write to file: {e}")

def main():
    app = QApplication(sys.argv)
    window = OilChangeLogApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
