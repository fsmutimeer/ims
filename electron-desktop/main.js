const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let djangoProcess = null;

function createWindow () {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false
    }
  });
  win.loadURL('http://localhost:8000');
}

function startDjango() {
  // Start Django server as a child process
  djangoProcess = spawn('python', [
    path.join('..', 'mobile_accessories', 'manage.py'),
    'runserver', '127.0.0.1:8000'
  ], {
    cwd: path.join(__dirname, '..'),
    shell: true,
    env: process.env
  });

  djangoProcess.stdout.on('data', (data) => {
    console.log(`[Django] ${data}`);
  });
  djangoProcess.stderr.on('data', (data) => {
    console.error(`[Django ERROR] ${data}`);
  });
}

app.whenReady().then(() => {
  startDjango();
  setTimeout(createWindow, 3000); // Wait for Django to start
});

app.on('window-all-closed', () => {
  if (djangoProcess) djangoProcess.kill();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
