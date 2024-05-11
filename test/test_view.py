import sys
from PyQt5.QtWidgets import QApplication
from src.view import View


class ShowUI:

    APP_ID = f'NYCU.Dentistry.SomaticApp'

    def main(self):
        self.config_taskbar_icon()
        app = QApplication(sys.argv)
        view = View()
        view.show()
        sys.exit(app.exec_())

    def config_taskbar_icon(self):
        try:
            from ctypes import windll  # only exists on Windows
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.APP_ID)
        except ImportError as e:
            print(e, flush=True)


if __name__ == '__main__':
    ShowUI().main()
