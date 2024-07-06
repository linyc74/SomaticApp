from os.path import dirname
from typing import List, Dict, Union
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, \
    QPushButton, QScrollArea, QCheckBox, QMessageBox, QFileDialog, QDialog, QFormLayout, \
    QLineEdit, QDialogButtonBox
from .model import DEFAULT_COMPUTE_PARAMETERS, DEFAULT_NAS_PARAMETERS, DEFAULT_PIPELINE_PARAMETERS


COMPUTE_TITLE = 'COMPUTE'
NAS_TITLE = 'NAS'
PIPELINE_TITLE = 'PIPELINE'
BUTTON_KEY_TO_LABEL = {
    'load_parameters': 'Load Parameters',
    'save_parameters': 'Save Parameters',
    'submit_jobs': 'Submit Jobs',
}


class Edit:

    key: str
    qlabel: QLabel
    qedit: Union[QComboBox, QCheckBox]

    def __init__(self, key: str, qlabel: QLabel, qedit: Union[QComboBox, QCheckBox]):
        self.key = key
        self.qlabel = qlabel
        self.qedit = qedit


class Button:

    key: str
    qbutton: QPushButton

    def __init__(self, key: str, qbutton: QPushButton):
        self.key = key
        self.qbutton = qbutton


class View(QWidget):

    TITLE = 'Somatic App'
    ICON_PNG = 'icon/logo.ico'
    WIDTH, HEIGHT = 800, 1000

    title_to_edits: Dict[str, List[Edit]]
    buttons: List[Button]

    question_layout: QVBoxLayout
    button_layout: QHBoxLayout
    scroll_area: QScrollArea
    scroll_contents: QWidget
    main_layout: QVBoxLayout

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.TITLE)
        self.setWindowIcon(QIcon(f'{dirname(dirname(__file__))}/{self.ICON_PNG}'))
        self.resize(self.WIDTH, self.HEIGHT)

        self.__init_title_to_edits()
        self.__init_buttons()

        self.__init_question_layout()
        self.__init_button_layout()
        self.__init_scroll_area_and_contents()
        self.__init_main_layout()
        self.__init_methods()

    def __init_title_to_edits(self):
        self.title_to_edits = {}
        for title, default_parameters in [
            (COMPUTE_TITLE, DEFAULT_COMPUTE_PARAMETERS),
            (NAS_TITLE, DEFAULT_NAS_PARAMETERS),
            (PIPELINE_TITLE, DEFAULT_PIPELINE_PARAMETERS),
        ]:
            edits = []
            for key, values in default_parameters.items():
                qlabel = QLabel(f'{key}:', self)

                if type(values) is bool:
                    qedit = QCheckBox(self)
                    qedit.setChecked(values)
                else:
                    qedit = QComboBox(self)
                    qedit.addItems([str(v) for v in values])
                    qedit.setEditable(True)

                edit = Edit(key=key, qlabel=qlabel, qedit=qedit)
                edits.append(edit)
            self.title_to_edits[title] = edits

    def __init_buttons(self):
        self.buttons = []
        for key, label in BUTTON_KEY_TO_LABEL.items():
            qbutton = QPushButton(label, self)
            button = Button(key=key, qbutton=qbutton)
            self.buttons.append(button)

    def __init_question_layout(self):
        self.question_layout = QVBoxLayout()

        for title, edits in self.title_to_edits.items():
            if len(self.question_layout) > 0:
                self.question_layout.addWidget(QLabel(' ', self))  # spacer

            label = QLabel(title, self)
            label.setAlignment(Qt.AlignCenter)
            self.question_layout.addWidget(label)

            for edit in edits:
                self.question_layout.addWidget(edit.qlabel)
                self.question_layout.addWidget(edit.qedit)

    def __init_button_layout(self):
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch(1)
        self.question_layout.addLayout(self.button_layout)
        for button in self.buttons:
            self.button_layout.addWidget(button.qbutton)

    def __init_scroll_area_and_contents(self):
        self.scroll_area = QScrollArea(self)
        self.scroll_contents = QWidget(self.scroll_area)  # the QWidget with all items
        self.scroll_contents.setLayout(self.question_layout)
        self.scroll_area.setWidget(self.scroll_contents)  # set the scroll_area's widget to be scroll_contents
        self.scroll_area.setWidgetResizable(True)

    def __init_main_layout(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.scroll_area)  # add scroll_area to the main_layout
        self.setLayout(self.main_layout)

    def __init_methods(self):
        self.message_box_info = MessageBoxInfo(self)
        self.message_box_error = MessageBoxError(self)
        self.message_box_yes_no = MessageBoxYesNo(self)
        self.file_dialog_open = FileDialogOpen(self)
        self.file_dialog_save = FileDialogSave(self)
        self.password_dialog = PasswordDialog(self)

    def get_parameters(self) -> Dict[str, Union[str, bool]]:
        ret = {}
        for edits in self.title_to_edits.values():
            for edit in edits:
                q = edit.qedit
                if type(q) is QComboBox:
                    val = q.currentText()
                else:  # QCheckBox
                    val = q.isChecked()
                ret[edit.key] = val

        return ret

    def set_parameters(self, parameters: Dict[str, Union[str, bool]]):
        # Reset flags to False because
        #   when a flag is not present in parameters, it should be False
        for edits in self.title_to_edits.values():
            for edit in edits:
                q = edit.qedit
                if type(q) is QCheckBox:
                    q.setChecked(False)

        for edits in self.title_to_edits.values():
            for edit in edits:
                q = edit.qedit

                val = parameters.get(edit.key, None)
                if val is None:
                    continue

                if type(q) is QComboBox:
                    q.setCurrentText(val)
                elif type(q) is QCheckBox:
                    q.setChecked(True)  # when the key if present, the flag should be True


class MessageBox:

    TITLE: str
    ICON: QMessageBox.Icon

    box: QMessageBox

    def __init__(self, parent: QWidget):
        self.box = QMessageBox(parent)
        self.box.setWindowTitle(self.TITLE)
        self.box.setIcon(self.ICON)

    def __call__(self, msg: str):
        self.box.setText(msg)
        self.box.exec_()


class MessageBoxInfo(MessageBox):

    TITLE = 'Info'
    ICON = QMessageBox.Information


class MessageBoxError(MessageBox):

    TITLE = 'Error'
    ICON = QMessageBox.Warning


class MessageBoxYesNo(MessageBox):

    TITLE = ' '
    ICON = QMessageBox.Question

    def __init__(self, parent: QWidget):
        super(MessageBoxYesNo, self).__init__(parent)
        self.box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self.box.setDefaultButton(QMessageBox.No)

    def __call__(self, msg: str) -> bool:
        self.box.setText(msg)
        return self.box.exec_() == QMessageBox.Yes


class FileDialog:

    parent: QWidget

    def __init__(self, parent: QWidget):
        self.parent = parent


class FileDialogOpen(FileDialog):

    def __call__(self) -> str:
        d = QFileDialog(self.parent)
        d.resize(1200, 800)
        d.setWindowTitle('Open')
        d.setNameFilter('All Files (*.*);;CSV files (*.csv);;TSV files (*.tsv);;tab files (*.tab);;TXT files (*.txt)')
        d.selectNameFilter('CSV files (*.csv)')
        d.setOptions(QFileDialog.DontUseNativeDialog)
        d.setFileMode(QFileDialog.ExistingFile)  # only one existing file can be selected
        d.exec_()
        selected = d.selectedFiles()
        return selected[0] if len(selected) > 0 else ''


class FileDialogSave(FileDialog):

    def __call__(self, filename: str = '') -> str:
        d = QFileDialog(self.parent)
        d.resize(1200, 800)
        d.setWindowTitle('Save As')
        d.selectFile(filename)
        d.setNameFilter('All Files (*.*);;CSV files (*.csv);;TSV files (*.tsv);;tab files (*.tab);;TXT files (*.txt)')
        d.selectNameFilter('CSV files (*.csv)')
        d.setOptions(QFileDialog.DontUseNativeDialog)
        d.setAcceptMode(QFileDialog.AcceptSave)
        d.exec_()

        files = d.selectedFiles()

        name_filter = d.selectedNameFilter()
        ext = name_filter.split('(*')[-1].split(')')[0]  # e.g. 'CSV files (*.csv)' -> '.csv'

        if len(files) == 0:
            ret = ''
        else:
            ret = files[0]
            if not ret.endswith(ext):  # add file extension if not present
                ret += ext

        return ret


class PasswordDialog:

    LINE_TITLE = 'Password:'
    LINE_DEFAULT = ''

    parent: QWidget

    dialog: QDialog
    layout: QFormLayout
    line_edit: QLineEdit
    button_box: QDialogButtonBox

    def __init__(self, parent: QWidget):
        self.parent = parent
        self.__init_dialog()
        self.__init_layout()
        self.__init_line_edit()
        self.__init_button_box()

    def __init_dialog(self):
        self.dialog = QDialog(parent=self.parent)
        self.dialog.setWindowTitle(' ')

    def __init_layout(self):
        self.layout = QFormLayout(parent=self.dialog)

    def __init_line_edit(self):
        self.line_edit = QLineEdit(self.LINE_DEFAULT, parent=self.dialog)
        self.line_edit.setEchoMode(QLineEdit.Password)
        self.layout.addRow(self.LINE_TITLE, self.line_edit)

    def __init_button_box(self):
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self.dialog)
        self.button_box.accepted.connect(self.dialog.accept)
        self.button_box.rejected.connect(self.dialog.reject)
        self.layout.addWidget(self.button_box)

    def __call__(self) -> Union[str, tuple]:
        if self.dialog.exec_() == QDialog.Accepted:
            return self.line_edit.text()
        else:
            return ''
