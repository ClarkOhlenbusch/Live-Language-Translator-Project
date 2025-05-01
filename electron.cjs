const { app, BrowserWindow } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev'); // Helper to check if in development

function createWindow() {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800, // Adjust width as needed
    height: 600, // Adjust height as needed
    alwaysOnTop: true, // <--- Make the window always on top
    webPreferences: {
      // It's recommended to use a preload script for security,
      // but for simplicity now, we might enable nodeIntegration directly.
      // Consider using contextIsolation: true and a preload script later.
      nodeIntegration: true, 
      contextIsolation: false, 
      // preload: path.join(__dirname, 'preload.js') // Example if using preload
    },
    // frame: false, // Uncomment for a borderless window
    // transparent: true, // Uncomment for a transparent window (requires frame: false)
  });

  // Load the index.html of the app.
  // In development, load from Vite dev server; otherwise, load the built file.
  const loadURL = isDev
    ? 'http://localhost:5173' // Your Vite dev server URL
    : `file://${path.join(__dirname, '../dist/index.html')}`; // Path to built React app

  mainWindow.loadURL(loadURL);

  // Open the DevTools automatically if in development
  if (isDev) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  // Optional: Remove menu bar
  // mainWindow.setMenu(null); 
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// In this file, you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here. 