import sys
from PyQt5.QtWidgets import QApplication
from .view import View
from .io import IO
from .controller import Controller


VERSION = 'v1.0.0-beta.1'
STARTING_MESSAGE = f'''\
Somatic App {VERSION}
College of Dentistry, National Yang Ming Chiao Tung University (NYCU), Taiwan
Yu-Cheng Lin, DDS, MS, PhD (ylin@nycu.edu.tw)
'''


class EntryPoint:

    APP_ID = f'NYCU.Dentistry.SomaticApp.{VERSION}'

    io: IO
    view: View
    controller: Controller

    def main(self):
        self.config_taskbar_icon()

        app = QApplication(sys.argv)

        self.io = IO()
        self.view = View()
        self.controller = Controller(io=self.io, view=self.view)

        print(STARTING_MESSAGE, flush=True)

        sys.exit(app.exec_())

    def config_taskbar_icon(self):
        try:
            from ctypes import windll  # only exists on Windows
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.APP_ID)
        except ImportError as e:
            print(e, flush=True)
