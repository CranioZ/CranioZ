import json
import os
import sys

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
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
IGNORE_DIRS = {".git", ".venv", "__pycache__", ".idea", "build", "dist"}

# Extensões conhecidas (label amigável -> extensão real)
KNOWN_EXTENSIONS = [
    ("Python (.py)", ".py"),
    ("Qt Designer (.ui)", ".ui"),
    ("Markdown (.md)", ".md"),
    ("JSON (.json)", ".json"),
    ("Texto (.txt)", ".txt"),
    ("C (.c)", ".c"),
    ("Cabeçalho (.h)", ".h"),
    ("C++ (.cpp)", ".cpp"),
    ("C++ Header (.hpp)", ".hpp"),
    ("YAML (.yaml)", ".yaml"),
]

# Extensões marcadas por padrão (as originais do projeto)
DEFAULT_EXTENSIONS = [".py", ".ui", ".md"]


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------
class PackWorker(QThread):
    progress = Signal(str)
    done = Signal(bool, str)

    def __init__(self, root_dir, output_file, selected_dirs, extensions):
        super().__init__()
        self.root_dir = root_dir
        self.output_file = output_file
        self.selected_dirs = [os.path.abspath(p) for p in selected_dirs]
        self.extensions = tuple(extensions)

    def _is_selected(self, path):
        """True se 'path' está sob (ou é) algum diretório selecionado."""
        path = os.path.abspath(path)
        for sel in self.selected_dirs:
            if path == sel:
                return True
            if path.startswith(sel + os.sep):
                return True
        return False

    def run(self):
        try:
            self.progress.emit("Iniciando empacotamento seletivo...")

            total_files = 0
            output_abs = os.path.abspath(self.output_file)

            with open(self.output_file, "w", encoding="utf-8") as f:
                for root, dirs, files in os.walk(self.root_dir):
                    # Poda: ignora diretórios fixos e fora da seleção
                    dirs[:] = [
                        d
                        for d in dirs
                        if d not in IGNORE_DIRS
                        and self._is_selected(os.path.join(root, d))
                    ]

                    if not self._is_selected(root):
                        continue

                    for file in files:
                        if not file.endswith(self.extensions):
                            continue

                        path = os.path.join(root, file)

                        # Evita incluir o próprio arquivo de saída
                        if os.path.abspath(path) == output_abs:
                            continue

                        rel_path = os.path.relpath(path, self.root_dir)
                        rel_path = rel_path.replace(os.sep, "/")

                        self.progress.emit(f"Adicionando: {rel_path}")

                        f.write(f"\n{'=' * 70}\n")
                        f.write(f"FILE: {rel_path}\n")
                        f.write(f"{'=' * 70}\n\n")

                        try:
                            with open(
                                path, encoding="utf-8", errors="ignore"
                            ) as code_file:
                                f.write(code_file.read())
                            f.write("\n\n")
                        except Exception as e:
                            f.write(f"# Erro ao ler arquivo: {e}\n\n")

                        total_files += 1

            self.done.emit(
                True,
                f"Empacotamento concluído com sucesso!\n"
                f"Arquivos incluídos: {total_files}\n"
                f"Saída: {self.output_file}",
            )
        except Exception as e:
            self.done.emit(False, f"Erro: {e!s}")


# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------
class PackProjectGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CranioZ - Pack Project")
        self.resize(900, 700)

        # Defaults (sobrescritos por load_config)
        self.root_dir = "."
        self.output_file = "contexto.txt"
        self.last_selected = []

        self._build_ui()

        # Carrega config DEPOIS que os widgets existem
        self.load_config()
        self.root_edit.setText(self.root_dir)
        self.output_edit.setText(self.output_file)

        self.append_log("Interface carregada. Configurações restauradas do JSON.")
        self.build_tree()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        title = QLabel("CranioZ - Código do projeto")
        title.setStyleSheet("font-size: 26px; font-weight: bold; padding: 15px 0;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # === ESQUERDA ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # --- Configurações (raiz + saída) ---
        config_group = QGroupBox("Configurações")
        config_layout = QFormLayout()

        self.root_edit = QLineEdit()
        btn_root = QPushButton("Pasta Raiz")
        btn_root.clicked.connect(self.select_root_dir)
        root_hbox = QHBoxLayout()
        root_hbox.addWidget(self.root_edit)
        root_hbox.addWidget(btn_root)

        self.output_edit = QLineEdit()
        btn_output = QPushButton("Salvar como...")
        btn_output.clicked.connect(self.select_output_file)
        output_hbox = QHBoxLayout()
        output_hbox.addWidget(self.output_edit)
        output_hbox.addWidget(btn_output)

        config_layout.addRow("Pasta Raiz:", root_hbox)
        config_layout.addRow("Arquivo de Saída:", output_hbox)
        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)

        # --- Extensões como checkboxes ---
        ext_group = QGroupBox("Extensões a incluir")
        ext_layout = QVBoxLayout()

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(6)

        self.ext_checks = {}  # ext -> QCheckBox
        row = col = 0
        for label, ext in KNOWN_EXTENSIONS:
            cb = QCheckBox(label)
            cb.setChecked(ext in DEFAULT_EXTENSIONS)
            self.ext_checks[ext] = cb
            grid.addWidget(cb, row, col)
            col += 1
            if col == 2:
                col = 0
                row += 1

        ext_layout.addLayout(grid)

        extra_hbox = QHBoxLayout()
        extra_hbox.addWidget(QLabel("Outras:"))
        self.extra_extensions_edit = QLineEdit()
        self.extra_extensions_edit.setPlaceholderText(".svg, .qrc, ...")
        extra_hbox.addWidget(self.extra_extensions_edit)
        ext_layout.addLayout(extra_hbox)

        ext_group.setLayout(ext_layout)
        left_layout.addWidget(ext_group)

        # --- Estrutura de pastas ---
        folders_group = QGroupBox("Estrutura")
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

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        # --- Botões inferiores ---
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

    # ------------------------------------------------------------ Config
    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)

            self.root_dir = data.get("root_dir", ".")
            self.output_file = data.get("output_file", "contexto.txt")
            self.last_selected = data.get("selected_dirs", [])

            saved_exts = data.get("extensions")
            if saved_exts is None:
                saved_exts = list(DEFAULT_EXTENSIONS)

            # Normaliza: sempre com ponto
            saved_exts = [
                e if e.startswith(".") else "." + e for e in saved_exts
            ]

            known_set = {ext for _, ext in KNOWN_EXTENSIONS}
            for ext, cb in self.ext_checks.items():
                cb.setChecked(ext in saved_exts)

            extras = [e for e in saved_exts if e not in known_set]
            self.extra_extensions_edit.setText(", ".join(extras))

        except Exception as e:
            print(f"Aviso: não foi possível carregar {CONFIG_FILE}: {e}")

    def save_config(self):
        try:
            data = {
                "root_dir": self.root_edit.text().strip(),
                "output_file": self.output_edit.text().strip(),
                "selected_dirs": self.get_selected_relative_paths(),
                "extensions": self._parse_extensions(),
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível salvar: {e}")

    def _parse_extensions(self):
        """Lê checkboxes + campo 'Outras' e devolve lista normalizada."""
        exts = [ext for ext, cb in self.ext_checks.items() if cb.isChecked()]

        raw_extra = self.extra_extensions_edit.text().strip()
        if raw_extra:
            for part in raw_extra.replace(";", ",").split(","):
                part = part.strip()
                if not part:
                    continue
                if not part.startswith("."):
                    part = "." + part
                if part not in exts:
                    exts.append(part)

        return exts or list(DEFAULT_EXTENSIONS)

    # ------------------------------------------------------ Seleção árvore
    def get_selected_relative_paths(self):
        root = self.tree.topLevelItem(0)
        if not root:
            return []

        root_path = self.root_edit.text().strip()
        selected_rel = []

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

    def get_selected_dirs(self):
        root = self.tree.topLevelItem(0)
        root_path = os.path.abspath(self.root_edit.text().strip())
        if not root:
            return [root_path]

        selected = []

        def collect(item):
            if item.checkState(0) == Qt.Checked:
                path = item.data(0, Qt.UserRole)
                if path:
                    selected.append(os.path.abspath(path))
            for i in range(item.childCount()):
                collect(item.child(i))

        collect(root)
        return selected or [root_path]

    # ------------------------------------------------------- Ações UI
    def select_root_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta Raiz", self.root_edit.text()
        )
        if dir_path:
            self.root_edit.setText(dir_path)
            self.root_dir = dir_path
            self.build_tree()

    def select_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar como",
            self.output_edit.text(),
            "Text Files (*.txt);;All Files (*)",
        )
        if file_path:
            self.output_edit.setText(file_path)

    # --------------------------------------------------------- Árvore
    def build_tree(self):
        root_path = self.root_edit.text().strip()
        if not root_path or not os.path.exists(root_path):
            self.append_log("⚠️ Pasta raiz inválida.")
            return

        self.tree.blockSignals(True)
        try:
            self.tree.clear()
            root_name = os.path.basename(root_path) or root_path
            root_item = QTreeWidgetItem(self.tree, [root_name])
            root_item.setData(0, Qt.UserRole, root_path)
            root_item.setCheckState(0, Qt.Checked)

            self.add_subdirs(root_item, root_path)
            root_item.setExpanded(True)
        finally:
            self.tree.blockSignals(False)

        self.restore_selection()

    def add_subdirs(self, parent_item, parent_path):
        try:
            for item in sorted(os.listdir(parent_path)):
                full_path = os.path.join(parent_path, item)
                if os.path.isdir(full_path) and item not in IGNORE_DIRS:
                    child = QTreeWidgetItem(parent_item, [item])
                    child.setData(0, Qt.UserRole, full_path)
                    child.setCheckState(0, Qt.Checked)
                    self.add_subdirs(child, full_path)
        except Exception:
            pass

    def restore_selection(self):
        """Restaura marcações: marca quem está salvo E desmarca o resto."""
        root_path = self.root_edit.text().strip()
        root_item = self.tree.topLevelItem(0)
        if not root_item:
            return

        has_history = bool(self.last_selected)

        self.tree.blockSignals(True)
        try:
            def restore(item):
                full_path = item.data(0, Qt.UserRole)
                if full_path and has_history:
                    rel = os.path.relpath(full_path, root_path)
                    if rel == ".":
                        rel = ""
                    state = (
                        Qt.Checked if rel in self.last_selected else Qt.Unchecked
                    )
                    item.setCheckState(0, state)
                for i in range(item.childCount()):
                    restore(item.child(i))

            restore(root_item)
        finally:
            self.tree.blockSignals(False)

        self._refresh_parent_states()

    def on_item_changed(self, item, column):
        if column != 0:
            return

        self.tree.blockSignals(True)
        try:
            state = item.checkState(0)
            if state != Qt.PartiallyChecked:
                self._set_children_state(item, state)
        finally:
            self.tree.blockSignals(False)

        self._refresh_parent_states()

    def _set_children_state(self, item, state):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, state)
            self._set_children_state(child, state)

    def _refresh_parent_states(self):
        root = self.tree.topLevelItem(0)
        if not root:
            return

        self.tree.blockSignals(True)
        try:
            def refresh(item):
                for i in range(item.childCount()):
                    refresh(item.child(i))

                if item.childCount() == 0:
                    return

                states = [
                    item.child(i).checkState(0)
                    for i in range(item.childCount())
                ]
                if all(s == Qt.Checked for s in states):
                    item.setCheckState(0, Qt.Checked)
                elif all(s == Qt.Unchecked for s in states):
                    item.setCheckState(0, Qt.Unchecked)
                else:
                    item.setCheckState(0, Qt.PartiallyChecked)

            refresh(root)
        finally:
            self.tree.blockSignals(False)

    # ----------------------------------------------------------- Log
    def append_log(self, message):
        self.log_text.append(message)

    # -------------------------------------------------------- Packing
    def start_packing(self):
        root_dir = self.root_edit.text().strip()
        output_file = self.output_edit.text().strip()

        if not root_dir or not os.path.exists(root_dir):
            QMessageBox.warning(self, "Erro", "Pasta raiz não encontrada!")
            return
        if not output_file:
            QMessageBox.warning(self, "Erro", "Informe o arquivo de saída!")
            return

        extensions = self._parse_extensions()
        if not extensions:
            QMessageBox.warning(
                self, "Erro", "Selecione pelo menos uma extensão!"
            )
            return

        self.root_dir = root_dir
        selected_dirs = self.get_selected_dirs()

        self.pack_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log_text.clear()

        self.append_log(
            f"Iniciando empacotamento de {len(selected_dirs)} pasta(s)..."
        )
        self.append_log(f"Extensões: {', '.join(extensions)}")

        self.worker = PackWorker(
            root_dir, output_file, selected_dirs, extensions
        )
        self.worker.progress.connect(self.append_log)
        self.worker.done.connect(self.packing_finished)
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

    # -------------------------------------------------------- Fechamento
    def closeEvent(self, event):
        worker = getattr(self, "worker", None)
        if worker is not None and worker.isRunning():
            worker.wait()

        self.save_config()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = PackProjectGUI()
    window.show()
    sys.exit(app.exec())