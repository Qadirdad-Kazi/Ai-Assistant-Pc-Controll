const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Voice commands
  sendCommand: (command) => ipcRenderer.invoke('send-command', command),
  toggleListening: (listening) => ipcRenderer.invoke('toggle-listening', listening),
  
  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  
  // Event listeners
  onPythonMessage: (callback) => ipcRenderer.on('python-message', callback),
  onPythonError: (callback) => ipcRenderer.on('python-error', callback),
  
  // Remove listeners
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
});
