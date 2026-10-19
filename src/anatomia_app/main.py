from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .main_window import AnatomyWindow, apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Anatomia Viva 3D")
    apply_theme(app)
    window = AnatomyWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
