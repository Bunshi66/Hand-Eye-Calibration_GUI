from source.controllers.app_controller import AppController
from PyQt5.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)

    controller = AppController()
    controller.run()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()