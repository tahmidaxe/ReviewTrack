import sys
import os
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QPushButton, QStackedWidget, QTextEdit,
                             QLabel, QFrame)
from PyQt6.QtCore import Qt, QTimer

import ui_components


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReviewTrack")
        self.setFixedSize(800, 480)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Load stylesheet
        try:
            qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.qss")
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Stylesheet load failed: {e}")

        # log_box must exist before _setup_logger so we create a placeholder
        self.log_box = None

        # Root
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ────── SIDEBAR ──────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sb_lay = QVBoxLayout(sidebar)
        sb_lay.setContentsMargins(0, 0, 0, 6)
        sb_lay.setSpacing(2)

        # Logo
        logo = QLabel("  🔖  ReviewTrack")
        logo.setObjectName("sidebar_logo")
        logo.setFixedHeight(36)
        sb_lay.addWidget(logo)

        # Nav buttons
        nav_items = [
            ("🏠  Dashboard",    0),
            ("✉️  Invitations", 1),
            ("📋  Pending",      2),
            ("✅  Completed",    3),
        ]
        self.nav_buttons = []
        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx, b=btn: self._switch(i, b))
            sb_lay.addWidget(btn)
            self.nav_buttons.append(btn)

        sb_lay.addStretch()

        # Toggle log button (bottom of sidebar)
        btn_log = QPushButton("📜 Toggle Logs")
        btn_log.setObjectName("btn_toggle_log")
        btn_log.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_log.clicked.connect(self._toggle_logs)
        sb_lay.addWidget(btn_log)

        root.addWidget(sidebar)

        # ────── CONTENT AREA ──────
        content = QWidget()
        content.setStyleSheet("background: #0a1628;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # Top bar
        topbar = QWidget()
        topbar.setObjectName("topbar")
        tb_lay = QHBoxLayout(topbar)
        tb_lay.setContentsMargins(10, 0, 10, 0)
        self.topbar_title = QLabel("Overview")
        self.topbar_title.setObjectName("topbar_title")
        tb_lay.addWidget(self.topbar_title)
        tb_lay.addStretch()

        btn_exit = QPushButton("✕  EXIT")
        btn_exit.setObjectName("exit_button")
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exit.clicked.connect(self.close)
        tb_lay.addWidget(btn_exit)
        cl.addWidget(topbar)

        # Screen stack
        self.stack = QStackedWidget()
        self.screens = [
            ui_components.DashboardScreen(),
            ui_components.InvitationsScreen(),
            ui_components.PendingScreen(),
            ui_components.CompletedScreen(),
        ]
        self.screen_titles = ["Overview", "Invitations", "Pending Reviews", "Completed"]
        for s in self.screens:
            self.stack.addWidget(s)
        cl.addWidget(self.stack)

        # Live logger
        self.log_box = QTextEdit()
        self.log_box.setObjectName("live_logger")
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(80)
        self.log_box.setVisible(True)
        cl.addWidget(self.log_box)

        # NOW safe to hook up the logger (log_box exists)
        self._setup_logger()

        root.addWidget(content)

        # Default screen
        self._switch(0, self.nav_buttons[0])

        # Auto refresh every 5 s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(5000)

        logging.info("App started — 800×480 frameless")

    # ── logger setup ──
    def _setup_logger(self):
        root_log = logging.getLogger()
        root_log.setLevel(logging.DEBUG)
        if not any(isinstance(h, ui_components.LogHandler) for h in root_log.handlers):
            handler = ui_components.LogHandler(self._log_msg)
            handler.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%H:%M:%S"))
            root_log.addHandler(handler)

    def _log_msg(self, msg):
        if self.log_box is None:
            return
        self.log_box.append(msg)
        sb = self.log_box.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _toggle_logs(self):
        self.log_box.setVisible(not self.log_box.isVisible())

    # ── navigation ──
    def _switch(self, idx, btn):
        for b in self.nav_buttons:
            b.setChecked(False)
        btn.setChecked(True)
        self.stack.setCurrentIndex(idx)
        self.topbar_title.setText(self.screen_titles[idx])
        logging.info(f"Screen → {self.screen_titles[idx]}")
        self._refresh()

    def _refresh(self):
        w = self.stack.currentWidget()
        if hasattr(w, "refresh_data"):
            w.refresh_data()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
