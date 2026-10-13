import json
import os
import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

CONFIG_FILE = "folder_structure_config.json"

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".idea",
    "build",
    "dist",
}


class FolderStructureWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, root_dir, output_file, selected_dirs):
        super().__init__()
        self.root_dir = os.path.abspath(root_dir)
        self.output_file = output_file
        self.selected_dirs = [os.path.abspath(p) for p in selected_dirs]

    def run(self):
        try:
            self.progress.emit("Gerando estrutura de pastas...")

            lines = []

            root_name = os.path.basename(self.root_dir) or self.root_dir
            lines.append(root_name)

            self.build_structure(
                current_path=self.root_dir,
                lines=lines,
                prefix=""
            )

            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            self.finished.emit(
                True,
                f"✅ Estrutura gerada com sucesso!\nArquivo: {self.output_file}"
            )

        except Exception as e:
            self.finished.emit(False, str(e))

    def is_selected(self, path):
        path = os.path.abspath(path)

        return any(
            path == selected or path.startswith(selected + os.sep)
            for selected in self.selected_dirs
        )

    def build_structure(self, current_path, lines, prefix):
        try:
            items = sorted(os.listdir(current_path))
        except Exception:
            return

        visible_items = []

        for item in items:
            full_path = os.path.join(current_path, item)

            if os.path.isdir(full_path):
                if item in IGNORE_DIRS:
                    continue

                if not self.is_selected(full_path):
                    continue

                visible_items.append((item, full_path, True))

            else:
                if not self.is_selected(current_path):
                    continue

                visible_items.append((item, full_path, False))

        total = len(visible_items)

        for index, (name, full_path, is_dir) in enumerate(visible_items):
            is_last = index == total - 1

            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{name}")

            self.progress.emit(name)

            if is_dir:
                extension = "    " if is_last else "│   "

                self.build_structure(
                    current_path=full_path,
                    lines=lines,
                    prefix=prefix + extension
                )


class FolderStructureGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OpenCMF - Folder Structure")
        self.resize(1000, 700)

        self.root_dir = "../../utils"
        self.output_file = "folder_structure.txt"
        self.last_selected = []

        self.load_config()

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        title = QLabel("📁 OpenCMF - Folder Structure")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            padding: 14px;
        """)

        main_layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        config_group = QGroupBox("⚙️ Configurações")
        config_layout = QFormLayout()

        self.root_edit = QLineEdit(self.root_dir)

        btn_root = QPushButton("Selecionar Pasta")
        btn_root.clicked.connect(self.select_root_dir)

        root_layout = QHBoxLayout()
        root_layout.addWidget(self.root_edit)
        root_layout.addWidget(btn_root)

        self.output_edit = QLineEdit(self.output_file)

        btn_output = QPushButton("Salvar Como")
        btn_output.clicked.connect(self.select_output_file)

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(btn_output)

        config_layout.addRow("Pasta Raiz:", root_layout)
        config_layout.addRow("Arquivo Saída:", output_layout)

        config_group.setLayout(config_layout)

        left_layout.addWidget(config_group)

        tree_group = QGroupBox("📂 Pastas Selecionadas")
        tree_layout = QVBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Estrutura do Projeto")
        self.tree.itemChanged.connect(self.on_item_changed)

        tree_layout.addWidget(self.tree)

        btn_refresh = QPushButton("🔄 Atualizar")
        btn_refresh.clicked.connect(self.build_tree)

        tree_layout.addWidget(btn_refresh)

        tree_group.setLayout(tree_layout)

        left_layout.addWidget(tree_group)

        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        preview_group = QGroupBox("📋 Log")
        preview_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)

        preview_layout.addWidget(self.log_text)

        preview_group.setLayout(preview_layout)

        right_layout.addWidget(preview_group)

        splitter.addWidget(right_widget)

        btn_layout = QHBoxLayout()

        btn_save = QPushButton("💾 Salvar Configuração")
        btn_save.clicked.connect(self.save_config)

        self.generate_btn = QPushButton("📄 GERAR ESTRUTURA")
        self.generate_btn.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 12px;
        """)

        self.generate_btn.clicked.connect(self.start_generation)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(self.generate_btn)

        main_layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        main_layout.addWidget(self.progress_bar)

        self.append_log("Interface carregada.")

        self.build_tree()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return

        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)

            self.root_dir = data.get("root_dir", ".")
            self.output_file = data.get(
                "output_file",
                "folder_structure.txt"
            )

            self.last_selected = data.get("selected_dirs", [])

        except Exception:
            pass

    def save_config(self):
        try:
            data = {
                "root_dir": self.root_edit.text().strip(),
                "output_file": self.output_edit.text().strip(),
                "selected_dirs": self.get_selected_relative_paths(),
            }

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        except Exception as e:
            QMessageBox.warning(
                self,
                "Erro",
                str(e)
            )

    def select_root_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta",
            self.root_edit.text()
        )

        if directory:
            self.root_edit.setText(directory)
            self.build_tree()

    def select_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Estrutura",
            self.output_edit.text(),
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            self.output_edit.setText(file_path)

    def build_tree(self):
        root_path = self.root_edit.text().strip()

        if not os.path.exists(root_path):
            self.append_log("⚠️ Pasta inválida.")
            return

        self.tree.clear()

        root_name = os.path.basename(root_path) or root_path

        root_item = QTreeWidgetItem(self.tree, [root_name])
        root_item.setData(0, Qt.UserRole, root_path)
        root_item.setCheckState(0, Qt.Checked)

        self.add_subdirs(root_item, root_path)

        root_item.setExpanded(True)

        self.restore_selection()

    def add_subdirs(self, parent_item, parent_path):
        try:
            for item in sorted(os.listdir(parent_path)):
                full_path = os.path.join(parent_path, item)

                if not os.path.isdir(full_path):
                    continue

                if item in IGNORE_DIRS:
                    continue

                child = QTreeWidgetItem(parent_item, [item])

                child.setData(0, Qt.UserRole, full_path)
                child.setCheckState(0, Qt.Checked)

                self.add_subdirs(child, full_path)

        except Exception:
            pass

    def restore_selection(self):
        if not self.last_selected:
            return

        root_path = self.root_edit.text().strip()
        root_item = self.tree.topLevelItem(0)

        if not root_item:
            return

        def restore(item):
            full_path = item.data(0, Qt.UserRole)

            if full_path:
                rel = os.path.relpath(full_path, root_path)

                if rel == ".":
                    rel = ""

                if rel in self.last_selected:
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)

            for i in range(item.childCount()):
                restore(item.child(i))

        restore(root_item)

    def on_item_changed(self, item, column):
        state = item.checkState(0)

        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)

    def get_selected_dirs(self):
        selected = []

        root = self.tree.topLevelItem(0)

        if not root:
            return []

        def collect(item):
            if item.checkState(0) == Qt.Checked:
                path = item.data(0, Qt.UserRole)

                if path:
                    selected.append(os.path.abspath(path))

            for i in range(item.childCount()):
                collect(item.child(i))

        collect(root)

        return selected

    def get_selected_relative_paths(self):
        selected_rel = []

        root_item = self.tree.topLevelItem(0)

        if not root_item:
            return []

        root_path = self.root_edit.text().strip()

        def collect(item):
            if item.checkState(0) == Qt.Checked:
                full_path = item.data(0, Qt.UserRole)

                if full_path:
                    rel = os.path.relpath(full_path, root_path)

                    if rel == ".":
                        rel = ""

                    selected_rel.append(rel)

            for i in range(item.childCount()):
                collect(item.child(i))

        collect(root_item)

        return selected_rel

    def append_log(self, message):
        self.log_text.append(message)

    def start_generation(self):
        root_dir = self.root_edit.text().strip()
        output_file = self.output_edit.text().strip()

        if not os.path.exists(root_dir):
            QMessageBox.warning(
                self,
                "Erro",
                "Pasta raiz inválida."
            )
            return

        if not output_file:
            QMessageBox.warning(
                self,
                "Erro",
                "Informe o arquivo de saída."
            )
            return

        selected_dirs = self.get_selected_dirs()

        self.log_text.clear()

        self.append_log("Iniciando geração da estrutura...")

        self.generate_btn.setEnabled(False)

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.worker = FolderStructureWorker(
            root_dir=root_dir,
            output_file=output_file,
            selected_dirs=selected_dirs,
        )

        self.worker.progress.connect(self.append_log)
        self.worker.finished.connect(self.generation_finished)

        self.worker.start()

    def generation_finished(self, success, message):
        self.generate_btn.setEnabled(True)

        self.progress_bar.setVisible(False)

        self.append_log(message)

        if success:
            pass
        else:
            QMessageBox.critical(
                self,
                "Erro",
                message
            )

    def closeEvent(self, event):
        self.save_config()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    window = FolderStructureGUI()
    window.show()

    sys.exit(app.exec())
