# launcher.py
"""
Launcher pro EXE verzi Multi-Agent Demo Platform.
Spustí Streamlit a Flask backend, otevře prohlížeč.
FIXED: Funguje s PyInstaller bundle (sys._MEIPASS)
"""

import subprocess
import sys
import os
import webbrowser
import time
import threading
from pathlib import Path


# ============================================================================
# PYINSTALLER BUNDLE SUPPORT
# ============================================================================

def get_resource_path(relative_path):
    """
    Získá absolutní cestu k resource souboru.
    Funguje pro development i PyInstaller bundle.
    """
    try:
        # PyInstaller vytvoří temp složku a uloží cestu do _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Development mode
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Konfigurace
STREAMLIT_PORT = 8501
FLASK_PORT = 5000
APP_TITLE = "Multi-Agent Demo Platform"


class ColorPrint:
    """Barevný výstup do konzole"""

    @staticmethod
    def print_header(text):
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")

    @staticmethod
    def print_success(text):
        print(f"✅ {text}")

    @staticmethod
    def print_error(text):
        print(f"❌ {text}")

    @staticmethod
    def print_info(text):
        print(f"💡 {text}")

    @staticmethod
    def print_step(text):
        print(f"🔧 {text}")


def check_api_config():
    """
    Zkontroluje API konfiguraci v conf.py
    """
    try:
        conf_path = get_resource_path("conf.py")

        if not os.path.exists(conf_path):
            ColorPrint.print_error("conf.py nebyl nalezen!")
            ColorPrint.print_info("API konfigurace chybí")
            return False

        # Import conf.py pro ověření
        import importlib.util
        spec = importlib.util.spec_from_file_location("conf", conf_path)
        conf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conf)

        # Kontrola existence API klíčů
        if hasattr(conf, 'AZURE_OPENAI_API_KEY') and conf.AZURE_OPENAI_API_KEY:
            ColorPrint.print_success("API konfigurace nalezena")
            return True
        else:
            ColorPrint.print_error("API klíče nejsou nakonfigurovány v conf.py!")
            return False

    except Exception as e:
        ColorPrint.print_error(f"Chyba při kontrole konfigurace: {e}")
        return False


def start_flask_backend():
    """Spustí Flask backend v samostatném threadu"""
    def run_flask():
        try:
            ColorPrint.print_step("Spouštím Flask backend...")

            # Najdi chatbot_api.py v bundle
            api_path = get_resource_path("chatbot_api.py")
            print(api_path)
            if not os.path.exists(api_path):
                ColorPrint.print_error("chatbot_api.py nebyl nalezen v bundle!")
                ColorPrint.print_info("Webpage Assistant nebude fungovat")
                return

            # Spuštění Flask
            flask_process = subprocess.Popen(
                [sys.executable, api_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                # Důležité: nastavit working directory na _MEIPASS
                cwd=get_resource_path(".")
            )

            # Čekání na start
            time.sleep(3)

            if flask_process.poll() is None:
                ColorPrint.print_success(f"Flask backend běží na: http://localhost:{FLASK_PORT}")
            else:
                ColorPrint.print_error("Flask backend se nepodařilo spustit")
                stderr = flask_process.stderr.read().decode('utf-8', errors='ignore')
                if stderr:
                    print(f"Chyba: {stderr[:200]}")

        except Exception as e:
            ColorPrint.print_error(f"Chyba při spouštění Flask: {str(e)}")
            ColorPrint.print_info("Webpage Assistant nebude fungovat")

    # Spuštění v threadu
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    return flask_thread


def start_streamlit():
    """Spustí Streamlit aplikaci"""
    try:
        ColorPrint.print_step("Spouštím Streamlit aplikaci...")

        # Najdi app.py v bundle
        app_path = get_resource_path("app.py")

        if not os.path.exists(app_path):
            ColorPrint.print_error("app.py nebyl nalezen v bundle!")
            input("Stiskněte Enter pro ukončení...")
            sys.exit(1)

        # Otevření prohlížeče po 3 sekundách
        def open_browser():
            time.sleep(3)
            url = f"http://localhost:{STREAMLIT_PORT}"
            ColorPrint.print_success(f"Otevírám prohlížeč: {url}")
            webbrowser.open(url)

        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

        # Spuštění Streamlit
        ColorPrint.print_success(f"Streamlit běží na: http://localhost:{STREAMLIT_PORT}")
        print("\n" + "="*60)
        ColorPrint.print_info("Aplikace je připravená!")
        ColorPrint.print_info("Pro ukončení stiskněte Ctrl+C")
        print("="*60 + "\n")

        # Důležité: spustit z bundle directory
        os.chdir(get_resource_path("."))

        subprocess.run([
            sys.executable, "-m", "streamlit", "run", app_path,
            f"--server.port={STREAMLIT_PORT}",
            "--server.headless=true",
            "--server.address=0.0.0.0"
        ])

    except KeyboardInterrupt:
        ColorPrint.print_info("\nZastavuji aplikaci...")
    except Exception as e:
        ColorPrint.print_error(f"Chyba při spouštění Streamlit: {str(e)}")
        import traceback
        traceback.print_exc()
        input("\nStiskněte Enter pro ukončení...")
        sys.exit(1)


def main():
    """Hlavní funkce launcheru"""
    # Hlavička
    ColorPrint.print_header(APP_TITLE)

    print(f"🚀 Spouštím aplikaci...\n")

    # Debug info
    print(f"📁 Bundle directory: {get_resource_path('.')}")
    print(f"🐍 Python: {sys.executable}")
    print()

    # Kontrola API konfigurace
    #check_api_config()
    print()

    # Spuštění Flask backendu (na pozadí)
    flask_thread = start_flask_backend()

    # Malá prodleva
    time.sleep(2)

    # Spuštění Streamlit (hlavní proces)
    start_streamlit()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        ColorPrint.print_error(f"Kritická chyba: {str(e)}")
        import traceback
        traceback.print_exc()
        input("\nStiskněte Enter pro ukončení...")
        sys.exit(1)
