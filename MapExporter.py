import os
from PIL import Image
import sys
import traceback
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QTextEdit, QHBoxLayout, QProgressBar, QTabWidget, QLineEdit, QTabBar, QScrollArea, QGridLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDateTime
from PyQt5.QtGui import QIcon

def convert_png_to_ints(file_path):
    try:
        with open(file_path, 'rb') as file:
            byte_data = file.read()
        return list(byte_data)
    except Exception as e:
        raise RuntimeError(f"Error converting PNG to ints: {e}")

def write_ints_to_file(ints, image_name, output_filepath):
    try:
        with open(output_filepath, 'w', encoding='utf-8') as file:
            file.write(image_name + '\n')
            for num in ints:
                file.write(str(num) + '\n')
            file.write('~\n')
    except Exception as e:
        raise RuntimeError(f"Error writing ints to file: {e}")

def read_project_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.readlines()
    except Exception as e:
        raise RuntimeError(f"Error reading project file: {e}")

def read_map_cubes(map_data_path):
    map_cubes = []
    try:
        for filename in os.listdir(map_data_path):
            if filename.endswith(".mapCube"):
                file_path = os.path.join(map_data_path, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    map_cubes.append(file.readlines())
    except Exception as e:
        raise RuntimeError(f"Error reading map cubes: {e}")
    return map_cubes

def convert_jpg_to_png(jpg_path, png_path):
    try:
        with Image.open(jpg_path) as img:
            img.save(png_path, 'PNG')
        return True
    except Exception as e:
        raise RuntimeError(f"Error converting JPG to PNG: {e}")

def read_custom_textures(custom_textures_path):
    custom_textures = []
    try:
        for filename in os.listdir(custom_textures_path):
            if filename.endswith(".png"):
                file_path = os.path.join(custom_textures_path, filename)
                integer_data = convert_png_to_ints(file_path)
                image_name = os.path.splitext(filename)[0]
                custom_textures.append((image_name, integer_data))
            elif filename.endswith(".jpg"):
                jpg_path = os.path.join(custom_textures_path, filename)
                png_path = os.path.join(custom_textures_path, os.path.splitext(filename)[0] + ".png")
                if convert_jpg_to_png(jpg_path, png_path):
                    integer_data = convert_png_to_ints(png_path)
                    image_name = os.path.splitext(filename)[0]
                    custom_textures.append((image_name, integer_data))
    except Exception as e:
        raise RuntimeError(f"Error reading custom textures: {e}")
    return custom_textures

def create_gbmap_file(output_file_path, relevant_section, gbmap_ICON, gbmap_BANNER, gbmap_CUSTOMTEXTURES, mapCube_data, update_advanced_console, update_progress, update_action, map_name, map_description):
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            update_action.emit("Writing version to file")
            file.write("V2\n")

            update_action.emit("Writing relevant section to file")
            file.write((map_name or relevant_section[1]).strip() + '\n')
            file.write((map_description or relevant_section[2]).strip() + '\n')

            update_action.emit("Writing section delimiter")
            file.write("§\n")

            update_action.emit("Writing map cube and custom texture counts")
            file.write(f"{len(mapCube_data)}\n{len(gbmap_CUSTOMTEXTURES)}\n")

            update_action.emit("Writing remaining relevant section to file")
            file.writelines(line.strip() + '\n' for line in relevant_section[3:])

            update_action.emit("Writing section delimiter")
            file.write("§\n")

            update_action.emit("Writing icon data to file")
            file.writelines([str(num) + '\n' for num in gbmap_ICON])

            update_action.emit("Writing section delimiter")
            file.write("§\n")

            update_action.emit("Writing banner data to file")
            file.writelines([str(num) + '\n' for num in gbmap_BANNER])

            update_action.emit("Writing section delimiter")
            file.write("§\n")

            for idx, (image_name, integer_data) in enumerate(gbmap_CUSTOMTEXTURES):
                update_action.emit(f"Writing custom texture: {image_name}")
                file.write(image_name + '\n')
                for num in integer_data:
                    file.write(str(num) + '\n')
                file.write('~\n')
                update_progress.emit(int((idx + 1) / len(gbmap_CUSTOMTEXTURES) * 30))

            update_action.emit("Writing section delimiter")
            file.write("§\n")

            for idx, cube_data in enumerate(mapCube_data):
                update_action.emit(f"Writing map cube data {idx + 1}/{len(mapCube_data)}")
                file.writelines(cube_data)
                update_progress.emit(30 + int((idx + 1) / len(mapCube_data) * 70))
                time.sleep(0.01)

            update_action.emit("Writing final section delimiter")
            file.write("§\n")
    except Exception as e:
        update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Error creating gbmap file: {e}")
        raise RuntimeError(f"Error creating gbmap file: {e}")

class ScriptThread(QThread):
    update_basic_console = pyqtSignal(str)
    update_advanced_console = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    update_action = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, folder_path, output_file_path, map_name, map_description):
        super().__init__()
        self.folder_path = folder_path
        self.output_file_path = output_file_path
        self.map_name = map_name
        self.map_description = map_description
        self.running = True

    def run(self):
        try:
            self.update_basic_console.emit("Initializing script execution...")
            self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Initializing script execution...")

            map_data_path = os.path.join(self.folder_path, "MapData")
            custom_textures_path = os.path.join(self.folder_path, "CustomTextures")
            project_file_path = os.path.join(self.folder_path, "projectFile.gbi")
            icon_file_path = os.path.join(self.folder_path, "icon.png")
            banner_file_path = os.path.join(self.folder_path, "banner.png")

            self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Validating required files and folders...")
            if not (os.path.exists(map_data_path) and os.path.exists(custom_textures_path) and os.path.exists(project_file_path) and os.path.exists(icon_file_path) and os.path.exists(banner_file_path)):
                self.update_basic_console.emit("Critical files or folders are missing.")
                self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Critical files or folders are missing.")
                self.finished.emit()
                return

            self.update_basic_console.emit("Gathering project metadata...")
            self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Reading project file: {project_file_path}")
            relevant_section = read_project_file(project_file_path)

            self.update_basic_console.emit("Processing icon data...")
            self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Converting icon to ints: {icon_file_path}")
            gbmap_ICON = convert_png_to_ints(icon_file_path)

            self.update_basic_console.emit("Processing banner data...")
            self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Converting banner to ints: {banner_file_path}")
            gbmap_BANNER = convert_png_to_ints(banner_file_path)

            self.update_basic_console.emit("Gathering custom texture data...")
            self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Reading custom textures: {custom_textures_path}")
            gbmap_CUSTOMTEXTURES = read_custom_textures(custom_textures_path)

            self.update_basic_console.emit("Gathering map cube data...")
            self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Reading map cubes: {map_data_path}")
            mapCube_data = read_map_cubes(map_data_path)

            self.update_basic_console.emit("Compiling gbmap file...")
            self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Creating gbmap file: {self.output_file_path}")
            create_gbmap_file(self.output_file_path, relevant_section, gbmap_ICON, gbmap_BANNER, gbmap_CUSTOMTEXTURES, mapCube_data, self.update_advanced_console, self.update_progress, self.update_action, self.map_name, self.map_description)

            self.update_basic_console.emit("Map file creation successful!")
            self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Map file creation successful!")
        except Exception as e:
            self.update_basic_console.emit(f"Error encountered: {e}")
            self.update_advanced_console.emit(f"{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')} Error encountered: {e}")
            traceback.print_exc()
        self.finished.emit()

    def stop(self):
        self.running = False
        self.terminate()

class MapCreatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('GoreBox Map Exporter')
        self.setGeometry(100, 100, 800, 450)
        self.layout = QVBoxLayout()

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabBar().setShape(QTabBar.RoundedNorth)

        self.import_tab = QWidget()
        self.import_layout = QVBoxLayout()

        self.import_scroll_area = QScrollArea()
        self.import_scroll_area.setWidgetResizable(True)
        self.import_scroll_content = QWidget()
        self.import_scroll_layout = QGridLayout()

        self.import_scroll_content.setLayout(self.import_scroll_layout)
        self.import_scroll_area.setWidget(self.import_scroll_content)
        self.import_layout.addWidget(self.import_scroll_area)

        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.refresh_import_list)
        self.import_layout.addWidget(self.refresh_button, alignment=Qt.AlignLeft)

        self.import_tab.setLayout(self.import_layout)
        self.tab_widget.addTab(self.import_tab, "Import")

        self.export_tab = QWidget()
        self.export_layout = QVBoxLayout()

        self.folder_label = QLabel('Folder path')
        self.export_layout.addWidget(self.folder_label)
        self.folder_button = QPushButton('Browse')
        self.folder_button.clicked.connect(self.browse_folder)
        self.export_layout.addWidget(self.folder_button)

        self.output_label = QLabel('Output file')
        self.export_layout.addWidget(self.output_label)
        self.output_button = QPushButton('Browse')
        self.output_button.clicked.connect(self.browse_output_file)
        self.export_layout.addWidget(self.output_button)

        self.console_layout = QHBoxLayout()

        self.basic_console_layout = QVBoxLayout()
        self.basic_console_label = QLabel('Basic Console')
        self.basic_console_label.setAlignment(Qt.AlignCenter)
        self.basic_console_layout.addWidget(self.basic_console_label)
        self.basic_console = QTextEdit()
        self.basic_console.setReadOnly(True)
        self.basic_console_layout.addWidget(self.basic_console)
        self.console_layout.addLayout(self.basic_console_layout)

        self.advanced_console_layout = QVBoxLayout()
        self.advanced_console_label = QLabel('Advanced Console')
        self.advanced_console_label.setAlignment(Qt.AlignCenter)
        self.advanced_console_layout.addWidget(self.advanced_console_label)
        self.advanced_console = QTextEdit()
        self.advanced_console.setReadOnly(True)
        self.advanced_console_layout.addWidget(self.advanced_console)
        self.console_layout.addLayout(self.advanced_console_layout)

        self.export_layout.addLayout(self.console_layout)

        self.progress_layout = QHBoxLayout()
        self.progress_label = QLabel('Press Start To Export')
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_layout.addWidget(self.progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_layout.addWidget(self.progress_bar)
        self.export_layout.addLayout(self.progress_layout)

        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start_script)
        self.export_layout.addWidget(self.start_button)

        self.export_tab.setLayout(self.export_layout)
        self.tab_widget.addTab(self.export_tab, "Export")

        self.basic_info_tab = QWidget()
        self.basic_info_layout = QVBoxLayout()
        self.basic_info_layout.setSpacing(5)
        self.basic_info_layout.setContentsMargins(5, 5, 5, 5)

        self.map_name_label = QLabel('Map Name')
        self.basic_info_layout.addWidget(self.map_name_label)
        self.map_name_input = QLineEdit()
        self.map_name_input.setPlaceholderText('Leave empty for original name')
        self.basic_info_layout.addWidget(self.map_name_input)

        self.map_description_label = QLabel('Map Description')
        self.basic_info_layout.addWidget(self.map_description_label)
        self.map_description_input = QLineEdit()
        self.map_description_input.setPlaceholderText('Leave empty for original description')
        self.basic_info_layout.addWidget(self.map_description_input)

        self.basic_info_layout.addStretch(1)

        self.basic_info_tab.setLayout(self.basic_info_layout)
        self.tab_widget.addTab(self.basic_info_tab, "Basic Info")

        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

        self.folder_path = None
        self.output_file_path = None

        self.refresh_import_list()

    def browse_folder(self):
        options = QFileDialog.Options()
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)
        if folder_path:
            self.folder_path = folder_path
            self.folder_label.setText(f'Folder path: {folder_path}')

    def browse_output_file(self):
        options = QFileDialog.Options()
        default_file_name = "CustomMap.gbmap"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Output File", default_file_name, "GBMAP Files (*.gbmap)", options=options)
        if file_path:
            self.output_file_path = file_path
            self.output_label.setText(f'Output file: {file_path}')

    def start_script(self):
        if not self.folder_path or not self.output_file_path:
            QMessageBox.warning(self, "Warning", "Please select both the folder and the output file.")
            return
        self.basic_console.clear()
        self.advanced_console.clear()
        self.progress_label.setText('Starting Export')
        self.progress_bar.setValue(0)
        self.folder_button.setEnabled(False)
        self.output_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.map_name_input.setEnabled(False)
        self.map_description_input.setEnabled(False)
        self.start_button.setText('Exporting Map...')
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.cancel_script)

        map_name = self.map_name_input.text().strip() if self.map_name_input.text().strip() else None
        map_description = self.map_description_input.text().strip() if self.map_description_input.text().strip() else None

        self.script_thread = ScriptThread(self.folder_path, self.output_file_path, map_name, map_description)
        self.script_thread.update_basic_console.connect(self.update_basic_console)
        self.script_thread.update_advanced_console.connect(self.update_advanced_console)
        self.script_thread.update_progress.connect(self.update_progress)
        self.script_thread.update_action.connect(self.update_action)
        self.script_thread.finished.connect(self.script_finished)
        self.script_thread.start()

    def cancel_script(self):
        self.script_thread.stop()
        self.script_finished()

    def update_basic_console(self, message):
        self.basic_console.append(message)
        QApplication.processEvents()

    def update_advanced_console(self, message):
        self.advanced_console.append(message)
        QApplication.processEvents()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        QApplication.processEvents()

    def update_action(self, message):
        self.progress_label.setText(f'{message}')
        QApplication.processEvents()

    def script_finished(self):
        self.folder_button.setEnabled(True)
        self.output_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.map_name_input.setEnabled(True)
        self.map_description_input.setEnabled(True)
        self.start_button.setText('Start')
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.start_script)
        self.progress_label.setText('Press Start To Export')
        self.progress_bar.setValue(0)
        QMessageBox.information(self, "Success", "Map file created successfully!")

    def refresh_import_list(self):
        user_home = os.path.expanduser("~")
        map_projects_dir = os.path.join(user_home, "AppData", "LocalLow", "F2Games", "GoreBox", "MapProjects")

        if not os.path.exists(map_projects_dir):
            QMessageBox.warning(self, "Warning", "MapProjects directory does not exist.")
            return

        folders = [f for f in os.listdir(map_projects_dir) if os.path.isdir(os.path.join(map_projects_dir, f))]

        for i in reversed(range(self.import_scroll_layout.count())):
            widget = self.import_scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        for idx, folder in enumerate(folders):
            folder_path = os.path.join(map_projects_dir, folder)
            project_file_path = os.path.join(folder_path, "projectFile.gbi")
            icon_path = os.path.join(folder_path, "icon.png")

            if os.path.exists(project_file_path) and os.path.exists(icon_path):
                with open(project_file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                    label_text = lines[1].strip() if len(lines) > 1 else folder

                button = QPushButton()
                button.setFixedSize(80, 80)
                button.setStyleSheet("background-color: lightgray; border: 1px solid gray;")

                icon = QIcon(icon_path)
                button.setIcon(icon)
                button.setIconSize(button.size())

                button.clicked.connect(lambda checked, path=folder_path: self.on_folder_button_clicked(path))

                self.import_scroll_layout.addWidget(button, idx // 5 * 2, idx % 5)

                label = QLabel(label_text)
                label.setAlignment(Qt.AlignCenter)
                label.setWordWrap(True)
                self.import_scroll_layout.addWidget(label, idx // 5 * 2 + 1, idx % 5)

    def on_folder_button_clicked(self, folder_path):
        self.folder_path = folder_path
        self.folder_label.setText(f'Folder path: {folder_path}')
        self.tab_widget.setCurrentWidget(self.export_tab)

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        ex = MapCreatorApp()
        ex.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()


