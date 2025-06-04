const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: false
    },
    icon: path.join(__dirname, 'assets/icon.png'),
    titleBarStyle: 'hiddenInset',
    show: false
  });

  // Load the app
  mainWindow.loadFile('index.html');

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Start Python backend
  startPythonBackend();
}

function startPythonBackend() {
  try {
    pythonProcess = spawn('python', ['voice_backend.py'], {
      cwd: __dirname,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    pythonProcess.stdout.on('data', (data) => {
      console.log(`Python: ${data}`);
      // Forward Python messages to renderer
      if (mainWindow) {
        mainWindow.webContents.send('python-message', data.toString());
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python Error: ${data}`);
      if (mainWindow) {
        mainWindow.webContents.send('python-error', data.toString());
      }
    });

    pythonProcess.on('close', (code) => {
      console.log(`Python process exited with code ${code}`);
    });
  } catch (error) {
    console.error('Failed to start Python backend:', error);
  }
}

// App event listeners
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers
ipcMain.handle('send-command', async (event, command) => {
  try {
    // Send command to Python backend
    if (pythonProcess && pythonProcess.stdin.writable) {
      pythonProcess.stdin.write(JSON.stringify({ type: 'command', data: command }) + '\n');
      return { success: true };
    }
    return { success: false, error: 'Backend not available' };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('toggle-listening', async (event, listening) => {
  try {
    if (pythonProcess && pythonProcess.stdin.writable) {
      pythonProcess.stdin.write(JSON.stringify({ 
        type: 'toggle-listening', 
        data: { listening } 
      }) + '\n');
      return { success: true };
    }
    return { success: false, error: 'Backend not available' };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-settings', async (event) => {
  // Return default settings for now
  return {
    theme: 'dark',
    voiceGender: 'female',
    language: 'en',
    wakeWord: 'Hey Wolf'
  };
});

ipcMain.handle('save-settings', async (event, settings) => {
  try {
    if (pythonProcess && pythonProcess.stdin.writable) {
      pythonProcess.stdin.write(JSON.stringify({ 
        type: 'save-settings', 
        data: settings 
      }) + '\n');
      return { success: true };
    }
    return { success: false, error: 'Backend not available' };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Remove default menu
Menu.setApplicationMenu(null);
