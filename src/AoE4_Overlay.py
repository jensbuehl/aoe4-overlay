import subprocess
import sys
import webbrowser
from functools import partial
from types import TracebackType
from typing import Type

from PyQt5 import QtCore, QtGui, QtWidgets

from overlay.helper_func import file_path, pyqt_wait
from overlay.logging_func import get_logger
from overlay.settings import CONFIG_FOLDER, settings
from overlay.tab_main import TabWidget

logger = get_logger(__name__)

VERSION = "1.2.2"


def excepthook(exc_type: Type[BaseException], exc_value: Exception,
               exc_tback: TracebackType):
    """ Provides the top-most exception handling. Logs unhandled exceptions and cleanly shuts down the app."""
    # Log the exception
    logger.exception("Unhandled exception!",
                     exc_info=(exc_type, exc_value, exc_tback))
    # Try to save settings
    try:
        settings.save()
    except Exception:
        logger.exception("Failed to save settings")
    # Shut down other threads
    try:
        Main.centralWidget().stop_checking_api()
    except Exception:
        pass
    sys.exit()


sys.excepthook = excepthook


class MainApp(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initUI()
        self.centralWidget().start()

    def initUI(self):
        self.setWindowTitle(f"AoE IV: Overlay ({VERSION})")
        self.setWindowIcon(QtGui.QIcon(file_path('img/icon.ico')))
        self.setGeometry(0, 0, settings.app_width, settings.app_height)
        self.move(QtWidgets.QDesktopWidget().availableGeometry().center() -
                  QtCore.QPoint(int(self.width() / 2), int(self.height() / 2)))

        # Create central widget
        self.setCentralWidget(TabWidget(self, VERSION))

        ### Create menu bar items
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        graphs_menu = menubar.addMenu('Graphs')
        link_menu = menubar.addMenu('Links')

        # Html
        icon = self.style().standardIcon(
            getattr(QtWidgets.QStyle, 'SP_DirLinkIcon'))
        htmlAction = QtWidgets.QAction(icon, 'Html files', self)
        htmlAction.setStatusTip('Open the folder with HTML layout files')
        htmlAction.triggered.connect(
            lambda: subprocess.run(['explorer', file_path("html")]))
        file_menu.addAction(htmlAction)

        # Config
        icon = self.style().standardIcon(
            getattr(QtWidgets.QStyle, 'SP_DirLinkIcon'))
        htmlAction = QtWidgets.QAction(icon, 'Config/logs', self)
        htmlAction.setStatusTip('Open the folder with config files')
        htmlAction.triggered.connect(
            lambda: subprocess.run(['explorer', CONFIG_FOLDER]))
        file_menu.addAction(htmlAction)

        # Exit
        icon = self.style().standardIcon(
            getattr(QtWidgets.QStyle, 'SP_DialogCloseButton'))
        exitAction = QtWidgets.QAction(icon, 'Exit', self)
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtWidgets.qApp.quit)
        file_menu.addAction(exitAction)

        # Github
        icon = QtGui.QIcon(file_path("img/github.png"))
        githubAction = QtWidgets.QAction(icon, 'App on Github', self)
        githubAction.triggered.connect(
            partial(webbrowser.open,
                    "https://github.com/FluffyMaguro/AoE4_Overlay"))
        link_menu.addAction(githubAction)

        # Discord
        icon = QtGui.QIcon(file_path("img/discord.png"))
        mdiscordAction = QtWidgets.QAction(icon, 'My discord', self)
        mdiscordAction.triggered.connect(
            partial(webbrowser.open, "https://discord.gg/FtGdhqD"))
        link_menu.addAction(mdiscordAction)

        # Maguro
        icon = QtGui.QIcon(file_path("img/maguro.jpg"))
        maguroAction = QtWidgets.QAction(icon, 'Maguro.one', self)
        maguroAction.triggered.connect(
            partial(webbrowser.open, "https://www.maguro.one/"))
        link_menu.addAction(maguroAction)

        # Paypal
        icon = QtGui.QIcon(file_path("img/paypal.png"))
        paypalAction = QtWidgets.QAction(icon, 'Donate', self)
        paypalAction.triggered.connect(
            partial(webbrowser.open,
                    "https://www.paypal.com/paypalme/FluffyMaguro"))
        link_menu.addAction(paypalAction)

        # AoEIV.net
        icon = QtGui.QIcon(file_path("img/aoeivnet.png"))
        aoe4netaction = QtWidgets.QAction(icon, 'AoEIV.net', self)
        aoe4netaction.triggered.connect(
            partial(webbrowser.open, "https://aoeiv.net/"))
        link_menu.addAction(aoe4netaction)

        # AoE4 World
        icon = QtGui.QIcon(file_path("img/aoe4worldcom.ico"))
        aoe4worldaction = QtWidgets.QAction(icon, 'AoE4 World', self)
        aoe4worldaction.triggered.connect(
            partial(webbrowser.open, "https://aoe4world.com/"))
        link_menu.addAction(aoe4worldaction)

        # Which graphs to show
        self.show_graph_actions = []
        for i in (1, 2, 3, 4):
            action = QtWidgets.QAction(f'Show {i}v{i}', self)
            self.show_graph_actions.append(action)
            action.setCheckable(True)
            action.setChecked(True)
            action.changed.connect(
                partial(self.centralWidget().graph_tab.change_plot_visibility,
                        i - 1, action))
            action.setChecked(settings.show_graph[str(i)])
            graphs_menu.addAction(action)

        lastday = QtWidgets.QAction("Last 24h", self)
        lastday.setCheckable(True)
        lastday.changed.connect(
            partial(self.centralWidget().graph_tab.limit_to_day, lastday))
        graphs_menu.addAction(lastday)
        self.show()

    def update_title(self, name: str):
        self.setWindowTitle(f"AoE IV: Overlay ({VERSION}) – {name}")

    def finish(self):
        """ Give it some time to stop everything correctly"""
        settings.app_width = self.width()
        settings.app_height = self.height()
        for i, action in enumerate(self.show_graph_actions):
            settings.show_graph[str(i + 1)] = action.isChecked()
        settings.save()
        self.centralWidget().stop_checking_api()
        pyqt_wait(1000)


if __name__ == '__main__':
    settings.load()
    app = QtWidgets.QApplication(sys.argv)
    Main = MainApp()
    exit_event = app.exec_()
    Main.finish()
    sys.exit(exit_event)
