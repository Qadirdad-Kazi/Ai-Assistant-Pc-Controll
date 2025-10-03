process.on('uncaughtException', (error) => {
  console.error('Main Uncaught Exception:', error);
  // Optionally, you might want to quit the app or log to a file
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Main Unhandled Rejection at:', promise, 'reason:', reason);
  // Optionally, you might want to quit the app or log to a file
});

const { app, BrowserWindow, ipcMain, Menu, systemPreferences, ipcRenderer } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { PythonShell } = require('python-shell');

// Screen reader state
let screenReaderActive = false;
let screenReaderPaused = false;
let screenReaderInterval = null;
let screenReaderPython = null;

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
    // Clean up screen reader
    if (screenReaderInterval) {
      clearInterval(screenReaderInterval);
      screenReaderInterval = null;
    }
    if (screenReaderPython) {
      screenReaderPython.end(() => {
        screenReaderPython = null;
      });
    }
    mainWindow = null;
  });

  // Start Python backend
  startPythonBackend();
}

function startPythonBackend() {
  try {
    // Resolve Python path: prefer .venv, then venv, then fallback to python3 in PATH
    const candidates = [
      path.join(__dirname, '..', '.venv', 'bin', 'python'),
      path.join(__dirname, '..', 'venv', 'bin', 'python'),
      path.join(__dirname, '..', '.venv', 'bin', 'python3'),
      path.join(__dirname, '..', 'venv', 'bin', 'python3'),
      process.env.PYTHON_PATH || 'python3',
      'python3'
    ];

    let pythonPath = candidates.find(p => {
      try {
        return fs.existsSync(p);
      } catch (e) {
        return false;
      }
    }) || 'python3';

    console.log('Using Python from:', pythonPath);
    
    websocketProcess = spawn(pythonPath, ['-u', 'websocket_server.py'], {
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
          console.log('Port 5001 is already in use. Trying to restart...');
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
    pythonProcess = spawn(pythonPath, ['voice_backend.py'], {
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

// Screen Reader Functions
function startScreenReader(interval = 2000) {
  return new Promise((resolve, reject) => {
    try {
      if (screenReaderPython) {
        screenReaderPython.end();
      }

      const options = {
        mode: 'json',
        pythonPath: 'python3', // or 'python' on Windows
        scriptPath: __dirname,
        args: ['--interval', interval]
      };

      screenReaderPython = PythonShell.run('screen_reader.py', options, (err, results) => {
        if (err) {
          console.error('Screen reader error:', err);
          screenReaderActive = false;
          mainWindow.webContents.send('screen-reader-update', {
            success: false,
            message: 'Failed to start screen reader',
            type: 'screen_reader_error'
          });
          reject(err);
        }
      });

      screenReaderPython.on('message', (message) => {
        try {
          const data = JSON.parse(message);
          mainWindow.webContents.send('screen-reader-update', data);
        } catch (e) {
          console.error('Error parsing screen reader message:', e);
        }
      });

      screenReaderActive = true;
      screenReaderPaused = false;
      
      resolve({
        success: true,
        message: 'Screen reader started',
        type: 'screen_reader',
        status: 'started'
      });
    } catch (error) {
      console.error('Error starting screen reader:', error);
      reject(error);
    }
  });
}

function stopScreenReader() {
  return new Promise((resolve) => {
    if (screenReaderPython) {
      screenReaderPython.end(() => {
        screenReaderPython = null;
        screenReaderActive = false;
        screenReaderPaused = false;
        resolve({
          success: true,
          message: 'Screen reader stopped',
          type: 'screen_reader',
          status: 'stopped'
        });
      });
    } else {
      screenReaderActive = false;
      screenReaderPaused = false;
      resolve({
        success: true,
        message: 'Screen reader was not running',
        type: 'screen_reader',
        status: 'stopped'
      });
    }
  });
}

// IPC Handlers for screen reader
ipcMain.handle('screen-reader', async (event, data) => {
  try {
    switch (data.action) {
      case 'start':
        return await startScreenReader(data.interval || 2000);
      case 'stop':
        return await stopScreenReader();
      case 'toggle-pause':
        screenReaderPaused = !screenReaderPaused;
        return {
          success: true,
          message: screenReaderPaused ? 'Screen reader paused' : 'Screen reader resumed',
          type: 'screen_reader',
          status: screenReaderPaused ? 'paused' : 'resumed',
          is_paused: screenReaderPaused
        };
      case 'status':
        return {
          success: true,
          is_running: screenReaderActive,
          is_paused: screenReaderPaused,
          type: 'screen_reader_status'
        };
      default:
        return {
          success: false,
          message: 'Invalid action',
          type: 'screen_reader_error'
        };
    }
  } catch (error) {
    console.error('Screen reader IPC error:', error);
    return {
      success: false,
      message: error.message,
      type: 'screen_reader_error'
    };
  }
});

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
