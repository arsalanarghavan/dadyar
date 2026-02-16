"""
دادیار هوشمند — Launcher
Starts the Streamlit server and opens the browser automatically.
This file is the entry point for PyInstaller builds.
"""

import sys
import os
import socket
import subprocess
import threading
import time
import webbrowser
from pathlib import Path


def _get_base_dir() -> Path:
    """Get the base directory (works both in dev and PyInstaller bundle)."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _find_free_port(start: int = 8501, end: int = 8599) -> int:
    """Find a free port in the given range."""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


def _open_browser(port: int, max_wait: int = 30):
    """Wait for the server to be ready, then open the browser."""
    for _ in range(max_wait * 2):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                webbrowser.open(f"http://localhost:{port}")
                return
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)


def main():
    base_dir = _get_base_dir()
    port = _find_free_port()

    # Set environment variables
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_THEME_BASE"] = "dark"

    app_py = str(base_dir / "app.py")

    print(f"🚀 دادیار هوشمند در حال اجرا روی http://localhost:{port}")
    print("   برای خروج Ctrl+C بزنید.")

    # Open browser in background thread
    threading.Thread(target=_open_browser, args=(port,), daemon=True).start()

    # Launch Streamlit
    if getattr(sys, "frozen", False):
        # Inside PyInstaller bundle — run streamlit via its Python API
        sys.argv = [
            "streamlit", "run", app_py,
            "--server.port", str(port),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--global.developmentMode", "false",
        ]
        from streamlit.web.cli import main as st_main
        st_main()
    else:
        # Dev mode — subprocess
        cmd = [
            sys.executable, "-m", "streamlit", "run", app_py,
            "--server.port", str(port),
            "--server.headless", "true",
        ]
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n👋 خداحافظ!")


if __name__ == "__main__":
    main()
