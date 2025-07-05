# TeknixorDV Inventory Management System

A modern Django-based inventory management system for mobile accessories, featuring:

- Business analytics dashboard (with interactive charts)
- Product, order, and category management
- Professional admin interface
- Beautiful public welcome page

## Features

- Django 5.2, Python 3.11
- SQLite by default (easy to switch to Postgres/MySQL)
- Email support (configurable via `.env`)
- Dockerized for easy deployment

---

## Quick Start (Docker)

### 1. Build the Docker image

```sh
docker build -t teknixordv-inventory .
```

### 2. Run the container

```sh
docker run --env-file .env -p 8000:8000 teknixordv-inventory
```

- The app will be available at: [http://localhost:8000](http://localhost:8000)
- The Django admin is at: [http://localhost:8000/admin/](http://localhost:8000/admin/)

### 3. Default Database

- Uses SQLite by default (file stored in the container).
- To use Postgres or MySQL, set the appropriate environment variables (see below).

---

## Environment Variables

Set these in your `.env` file (copied automatically into the container):

```
EMAIL_BACKEND=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=yourpassword
DEFAULT_FROM_EMAIL=your@email.com
```

For Postgres (example):

```
DATABASE_URL=postgres://user:password@host:5432/dbname
```

---

## Development (without Docker)

1. **Activate your virtual environment:**
   - **Windows (CMD):**
     ```sh
     env\Scripts\activate
     ```
   - **Windows (PowerShell):**
     ```sh
     env\Scripts\Activate.ps1
     ```
   - **macOS/Linux:**
     ```sh
     source env/bin/activate
     ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Copy `.env` to the project root** (if not already present).
4. **Run the development server:**
   ```sh
   python mobile_accessories/manage.py runserver
   ```

---

## Admin Access

- Create a superuser (first time only):
  ```sh
  docker exec -it <container_id> python mobile_accessories/manage.py createsuperuser
  ```
- Or, locally: `python mobile_accessories/manage.py createsuperuser`

---

## License

© 2025 Teknixor DV. All rights reserved.

---

## Contact

- Email: info@teknixor.com

---

## Native Desktop App (PyInstaller + pywebview)

You can run the app as a true native desktop application (no browser, no Electron required):

### 1. All dependencies are already included in your requirements file.

_You do not need to install `pyinstaller` or `pywebview` manually—they are already included._

### 2. Run the desktop app (for development):

```sh
python desktop.py
```

### 3. Build a standalone executable (for distribution):

```sh
pyinstaller --onefile --noconsole desktop.py
```

- The output will be in the `dist/` folder as `desktop.exe` (Windows) or just `desktop` (Mac/Linux).
- Distribute this file to your users—they just double-click to run the app.

### 4. (Optional) Custom icon:

Add `--icon=icon.ico` to the PyInstaller command for a custom app icon.

---

## Do I need the electron-desktop folder?

**No.** If you are using the native desktop app approach (PyInstaller + pywebview), you do NOT need the `electron-desktop` folder. You can safely delete it to keep your project clean.
