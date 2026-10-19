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

CONFIG_FILE = "pack_config.json"


class PackWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, root_dir, output_file, selected_dirs):
        super().__init__()
        self.root_dir = root_dir
        self.output_file = output_file
        self.selected_dirs = selected_dirs

    def run(self):
        try:
            ignore_dirs = {'.git', '.venv', '__pycache__', '.idea', 'build', 'dist'}
            extensions = {'.py', '.ui', '.md'}

            self.progress.emit("Iniciando empacotamento seletivo...")

            with open(self.output_file, 'w', encoding='utf-8') as f:
                for root, dirs, files in os.walk(self.root_dir):
                    dirs[:] = [d for d in dirs if d not in ignore_dirs]

                    current_abs = os.path.abspath(root)
                    if not any(current_abs.startswith(sel) for sel in self.selected_dirs):
                        continue

                    for file in files:
                        if any(file.endswith(ext) for ext in extensions):
                            path = os.path.join(root, file)
                            rel_path = os.path.relpath(path, self.root_dir)

                            self.progress.emit(f"Adicionando: {rel_path}")

                            f.write(f"\n{'=' * 70}\n")
                            f.write(f"FILE: {rel_path}\n")
                            f.write(f"{'=' * 70}\n\n")

                            try:
                                with open(path, encoding='utf-8', errors='ignore') as code_file:
                                    f.write(code_file.read())
                                f.write("\n\n")
                            except Exception as e:
                                f.write(f"# Erro ao ler arquivo: {e}\n\n")
        except Exception as e:
            self.finished.emit(False, f"Erro: {e!s}")


class PackProjectGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CranioZ - Documentation")
        self.resize(800, 600)

        self.root_dir = "."
        self.output_file = "docs.txt"
        self.last_selected = []  # caminhos relativos salvos

        self.load_config()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        title = QLabel("CranioZ - Documentação do projeto")
        title.setStyleSheet("font-size: 26px; font-weight: bold; padding: 15px 0;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # === ESQUERDA ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Configurações
        config_group = QGroupBox("Configurações")
        config_layout = QFormLayout()

        self.root_edit = QLineEdit(self.root_dir)
        btn_root = QPushButton("Pasta Raiz")
        btn_root.clicked.connect(self.select_root_dir)

        root_hbox = QHBoxLayout()
        root_hbox.addWidget(self.root_edit)
        root_hbox.addWidget(btn_root)

        self.output_edit = QLineEdit(self.output_file)
        btn_output = QPushButton("Salvar como...")
        btn_output.clicked.connect(self.select_output_file)

        output_hbox = QHBoxLayout()
        output_hbox.addWidget(self.output_edit)
        output_hbox.addWidget(btn_output)

        config_layout.addRow("Pasta Raiz:", root_hbox)
        config_layout.addRow("Arquivo de Saída:", output_hbox)
        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)

        # Lista de Pastas
        folders_group = QGroupBox("")
        folders_layout = QVBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Estrutura de Pastas")
        self.tree.itemChanged.connect(self.on_item_changed)
        folders_layout.addWidget(self.tree)

        btn_refresh = QPushButton("Atualizar")
        btn_refresh.clicked.connect(self.build_tree)
        folders_layout.addWidget(btn_refresh)

        folders_group.setLayout(folders_layout)
        left_layout.addWidget(folders_group)

        splitter.addWidget(left_widget)

        # === DIREITA: Log ===
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        splitter.addWidget(log_group)

        # Botões inferiores
        btn_layout = QHBoxLayout()
        self.pack_btn = QPushButton("Empacotar projeto")
        self.pack_btn.clicked.connect(self.start_packing)

        btn_save_config = QPushButton("Salvar Configs")
        btn_save_config.clicked.connect(self.save_config)

        btn_layout.addWidget(btn_save_config)
        btn_layout.addWidget(self.pack_btn)
        main_layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.append_log("Interface carregada. Configurações restauradas do JSON.")

        # Carregar árvore após inicialização
        self.build_tree()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, encoding='utf-8') as f:
                    data = json.load(f)
                    self.root_dir = data.get("root_dir", ".")
                    self.output_file = data.get("output_file", "contexto.txt")
                    self.last_selected = data.get("selected_dirs", [])
            except:
                pass

    def save_config(self):
        try:
            data = {
                "root_dir": self.root_edit.text().strip(),
                "output_file": self.output_edit.text().strip(),
                "selected_dirs": self.get_selected_relative_paths()
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível salvar: {e}")

    def get_selected_relative_paths(self):
        """Retorna caminhos relativos das pastas selecionadas"""
        selected_rel = []
        root = self.tree.topLevelItem(0)
        if not root:
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

        collect(root)
        return selected_rel

    def select_root_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta Raiz", self.root_edit.text())
        if dir_path:
            self.root_edit.setText(dir_path)
            self.build_tree()

    def select_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar como", self.output_edit.text(), "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.output_edit.setText(file_path)

    def build_tree(self):
        root_path = self.root_edit.text().strip()
        if not os.path.exists(root_path):
            self.append_log("⚠️ Pasta raiz inválida.")
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
                if os.path.isdir(full_path) and item not in {'.git', '.venv', '__pycache__', '.idea', 'build', 'dist'}:
                    child = QTreeWidgetItem(parent_item, [item])
                    child.setData(0, Qt.UserRole, full_path)
                    child.setCheckState(0, Qt.Checked)
                    self.add_subdirs(child, full_path)
        except:
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
            for i in range(item.childCount()):
                restore(item.child(i))

        restore(root_item)

    def on_item_changed(self, item, column):
        if item.childCount() > 0:
            state = item.checkState(0)
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, state)

    def get_selected_dirs(self):
        selected = []
        root = self.tree.topLevelItem(0)
        if not root:
            return [os.path.abspath(self.root_edit.text().strip())]

        def collect(item):
            if item.checkState(0) == Qt.Checked:
                path = item.data(0, Qt.UserRole)
                if path:
                    selected.append(os.path.abspath(path))
            for i in range(item.childCount()):
                collect(item.child(i))

        collect(root)
        return selected if selected else [os.path.abspath(self.root_edit.text().strip())]

    def append_log(self, message):
        self.log_text.append(message)

    def start_packing(self):
        root_dir = self.root_edit.text().strip()
        output_file = self.output_edit.text().strip()

        if not os.path.exists(root_dir):
            QMessageBox.warning(self, "Erro", "Pasta raiz não encontrada!")
            return
        if not output_file:
            QMessageBox.warning(self, "Erro", "Informe o arquivo de saída!")
            return

        selected_dirs = self.get_selected_dirs()

        self.pack_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log_text.clear()

        self.append_log(f"Iniciando empacotamento de {len(selected_dirs)} pasta(s)...")

        self.worker = PackWorker(root_dir, output_file, selected_dirs)
        self.worker.progress.connect(self.append_log)
        self.worker.finished.connect(self.packing_finished)
        self.worker.start()

    def packing_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.pack_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "Sucesso", message)
            self.append_log("✅ Empacotamento finalizado!")
        else:
            QMessageBox.critical(self, "Erro", message)

        self.append_log(message)

    def closeEvent(self, event):
        """Salva automaticamente ao fechar"""
        self.save_config()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = PackProjectGUI()
    window.show()
    sys.exit(app.exec())
