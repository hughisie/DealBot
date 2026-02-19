const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

if (!isDev) {
  try {
    // Start backend server in production
    require('./backend/index.js');
  } catch (err) {
    console.error('Failed to start backend:', err);
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 900,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
    titleBarStyle: 'hiddenInset', // Mac-style title bar
    backgroundColor: '#121121', // Match dark theme
  });

  if (isDev) {
    win.loadURL('http://localhost:5173');
  } else {
    win.loadFile(path.join(__dirname, 'frontend/dist/index.html'));
  }
}

app.whenReady().then(() => {
  createWindow();

  ipcMain.handle('pick-folder', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory', 'createDirectory'],
      title: 'Select Save Folder',
    });
    return result.canceled ? null : result.filePaths[0];
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
