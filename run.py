import os
import streamlit.web.cli as stcli
import sys
import threading
import shutil
from werkzeug.serving import make_server
from chatbot_api import app


def setup_streamlit_credentials():
    """Zkopíruje credentials.toml do domovského adresáře uživatele"""
    streamlit_dir = os.path.join(os.path.expanduser('~'), '.streamlit')
    credentials_file = os.path.join(streamlit_dir, 'credentials.toml')

    # Vytvoření adresáře pokud neexistuje
    os.makedirs(streamlit_dir, exist_ok=True)

    # Zkopírování credentials.toml pokud neexistuje
    if not os.path.exists(credentials_file):
        source_creds = os.path.join(os.path.dirname(__file__), '.streamlit', 'credentials.toml')
        if os.path.exists(source_creds):
            shutil.copy(source_creds, credentials_file)
            print("Streamlit credentials nakonfigurovány")


# Globální proměnné pro server a vlákno
flask_server = None
flask_thread = None


class ServerThread(threading.Thread):
    """Vlákno pro Flask server s možností elegantního ukončení"""

    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server
        self.daemon = True

    def run(self):
        """Spustí Flask server"""
        print("Flask API běží na http://localhost:5000")
        self.server.serve_forever()

    def shutdown(self):
        """Elegantně ukončí Flask server"""
        print("Ukončuji Flask server...")
        self.server.shutdown()


def start_flask():
    """Vytvoří a spustí Flask server"""
    global flask_server, flask_thread

    flask_server = make_server('localhost', 5000, app, threaded=True)
    flask_thread = ServerThread(flask_server)
    flask_thread.start()


def stop_flask():
    """Elegantně ukončí Flask server před vypnutím aplikace"""
    global flask_server, flask_thread

    if flask_thread and flask_thread.is_alive():
        flask_thread.shutdown()
        flask_thread.join(timeout=5)
        print("Flask server ukončen")


def run_streamlit():
    """Spustí Streamlit aplikaci"""
    os.chdir(os.path.dirname(__file__))

    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.port=8501",
        "--global.developmentMode=false",
    ]

    sys.exit(stcli.main())


if __name__ == "__main__":
    # Nastavení credentials před spuštěním Streamlitu
    setup_streamlit_credentials()

    import atexit

    atexit.register(stop_flask)

    # Spuštění Flask serveru
    start_flask()

    print("Streamlit se spouští na http://localhost:8501")

    # Spuštění Streamlit v hlavním vlákně
    try:
        run_streamlit()
    except KeyboardInterrupt:
        print("\nAplikace ukončena uživatelem")
    finally:
        stop_flask()
