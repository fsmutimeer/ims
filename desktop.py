import webview
import subprocess
import threading
import time
import os

def run_django():
    # Start Django server in a subprocess
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mobile_accessories.settings')
    subprocess.Popen(['python', 'mobile_accessories/manage.py', 'runserver', '127.0.0.1:8000'])
    # Wait for server to start
    time.sleep(3)

def main():
    # Start Django in a background thread
    threading.Thread(target=run_django, daemon=True).start()
    # Open the desktop window
    webview.create_window('TeknixorDV Inventory', 'http://127.0.0.1:8000', width=1200, height=800)
    webview.start()

if __name__ == '__main__':
    main()
