process.on('uncaughtException', (error) => {
  console.error('Main Uncaught Exception:', error);
  // Optionally, you might want to quit the app or log to a file
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Main Unhandled Rejection at:', promise, 'reason:', reason);
  // Optionally, you might want to quit the app or log to a file
});

const { app, BrowserWindow, ipcMain, Menu, systemPreferences } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;
let websocketProcess;

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
  mainWindow.loadFile(path.join(__dirname, 'index.html'));

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
    // Start the WebSocket server with unbuffered output
    websocketProcess = spawn('/Users/qadirdadkazi/Desktop/Currently Not Working/VoiceCompanion/venv/bin/python', ['-u', 'websocket_server.py'], {
      cwd: __dirname,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    websocketProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      if (output) {
        console.log(`WebSocket: ${output}`);
      }
    });

    websocketProcess.stderr.on('data', (data) => {
      const error = data.toString().trim();
      if (error) {
        console.error(`WebSocket Error: ${error}`);
        // Try to restart the WebSocket server if it crashes
        if (error.includes('Address already in use')) {
          console.log('Port 5000 is already in use. Trying to restart...');
          setTimeout(() => {
            if (websocketProcess) {
              websocketProcess.kill();
              startPythonBackend();
            }
          }, 2000);
        }
      }
    });

    websocketProcess.on('close', (code) => {
      console.log(`WebSocket server exited with code ${code}`);
      // Auto-restart the WebSocket server if it crashes
      if (code !== 0) {
        console.log('Restarting WebSocket server...');
        setTimeout(() => startPythonBackend(), 2000);
      }
    });

    // Start the voice backend
    pythonProcess = spawn('/Users/qadirdadkazi/Desktop/Currently Not Working/VoiceCompanion/venv/bin/python', ['voice_backend.py'], {
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
app.whenReady().then(async () => {
  try {
    const microphoneAccess = await systemPreferences.askForMediaAccess('microphone');
    if (microphoneAccess) {
      console.log('Microphone access granted by user.');
    } else {
      console.error('Microphone access denied by user.');
      // Optionally, inform the user through a dialog or by sending a message to renderer
      // For now, we'll rely on the renderer to display the error based on its checks
    }
  } catch (error) {
    console.error('Error requesting microphone permission:', error);
  }
  createWindow();
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (websocketProcess) {
    websocketProcess.kill();
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
  // TODO: Implement actual settings loading/saving from a file or store
  return {
    theme: 'dark',
    voiceGender: 'female',
    language: 'en',
    wakeWord: 'Hey Wolf',
    alwaysListen: false // Ensure all expected fields are present
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
