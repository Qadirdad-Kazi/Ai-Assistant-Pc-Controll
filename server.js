import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs/promises';

const execAsync = promisify(exec);

dotenv.config();

// Create express app
const app = express();

// Middleware - Enable CORS for all routes
app.use(cors());

// Parse JSON bodies (no need for body-parser in newer Express)
app.use(express.json());

// Log all requests
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

const PORT = process.env.PORT || 3001;

// Simple test route
app.get('/api/test', (req, res) => {
  console.log('Test endpoint hit');
  res.json({ status: 'Server is running', time: new Date().toISOString() });
});

// Allowed commands and their validations
const ALLOWED_COMMANDS = {
  'create folder': {
    pattern: /^create folder\s+(.+)$/i,
    handler: async (match) => {
      const folderName = match[1].trim();
      const folderPath = path.resolve(process.cwd(), folderName);
      await fs.mkdir(folderPath, { recursive: true });
      return { output: `✓ Created folder: ${folderName}`, path: folderPath };
    }
  },
  'create file': {
    pattern: /^(?:create file|write)\s+([^\s]+)(?:\s+with\s+)?(.*)?/i,
    handler: async (match) => {
      const fileName = match[1].trim();
      const content = match[2]?.trim() || '';
      const filePath = path.resolve(process.cwd(), fileName);
      await fs.writeFile(filePath, content, 'utf8');
      return { output: `✓ Created file: ${fileName}${content ? ' with content' : ''}`, path: filePath };
    }
  },
  'list files': {
    pattern: /^list files(?: in )?(.*)?$/i,
    handler: async (match) => {
      const dir = match[1] ? path.resolve(process.cwd(), match[1].trim()) : process.cwd();
      const files = await fs.readdir(dir, { withFileTypes: true });
      const fileList = files.map(file => ({
        name: file.name,
        type: file.isDirectory() ? 'directory' : 'file',
        path: path.join(dir, file.name)
      }));
      return { 
        output: `📂 Contents of ${dir}:\n${fileList.map(f => `  ${f.type === 'directory' ? '📁' : '📄'} ${f.name}`).join('\n')}`,
        files: fileList
      };
    }
  },
  'execute': {
    pattern: /^execute\s+(.+)$/i,
    handler: async (match) => {
      const cmd = match[1].trim();
      const { stdout, stderr } = await execAsync(cmd, { cwd: process.cwd() });
      if (stderr) throw new Error(stderr);
      return { output: `✓ Command executed successfully\n${stdout}` };
    }
  },
  'navigate': {
    pattern: /^navigate\s+(.+)$/i,
    handler: async (match) => {
      const newPath = match[1].trim();
      const targetPath = path.resolve(process.cwd(), newPath);
      
      try {
        await fs.access(targetPath);
        process.chdir(targetPath);
        return { output: `✓ Changed directory to: ${targetPath}`, path: targetPath };
      } catch (error) {
        throw new Error(`Directory not found: ${targetPath}`);
      }
    }
  },
  'open': {
    pattern: /^open\s+(.+)$/i,
    handler: async (match) => {
      // Use dynamic import for ES modules
      const { exec } = await import('node:child_process');
      const { promisify } = await import('node:util');
      const execPromise = promisify(exec);
      
      const target = match[1].toLowerCase().trim();
      
      // Map common locations to their respective shell commands
      const locations = {
        'my computer': 'explorer "This PC"',
        'documents': 'explorer "%USERPROFILE%\\Documents"',
        'downloads': 'explorer "%USERPROFILE%\\Downloads"',
        'desktop': 'explorer "%USERPROFILE%\\Desktop"',
        'pictures': 'explorer "%USERPROFILE%\\Pictures"',
        'videos': 'explorer "%USERPROFILE%\\Videos"',
        'music': 'explorer "%USERPROFILE%\\Music"',
        'recycle bin': 'explorer shell:RecycleBinFolder',
        'control panel': 'control',
        'settings': 'start ms-settings:'
      };

      try {
        if (locations[target]) {
          console.log(`Opening system location: ${target}`);
          const command = process.platform === 'win32' ? 
            `cmd /c ${locations[target]}` : 
            `xdg-open "${locations[target]}"`;
          
          const { stdout, stderr } = await execPromise(command);
          if (stderr) console.error('Command stderr:', stderr);
          return { output: `✓ Opened: ${target}` };
          
        } else if (await fs.access(target).then(() => true).catch(() => false)) {
          // For direct file/folder paths
          console.log(`Opening path: ${target}`);
          const absPath = path.resolve(target);
          const openCommand = process.platform === 'win32' ? 
            `explorer "${absPath}"` : 
            `xdg-open "${absPath}"`;
            
          const { stdout, stderr } = await execPromise(openCommand);
          if (stderr) console.error('Open path stderr:', stderr);
          return { output: `✓ Opened: ${target}` };
          
        } else if (target.startsWith('http://') || target.startsWith('https://')) {
          // For web URLs
          console.log(`Opening URL: ${target}`);
          const openCommand = process.platform === 'win32' ? 
            `start ${target}` : 
            `xdg-open "${target}"`;
            
          const { stdout, stderr } = await execPromise(openCommand);
          if (stderr) console.error('Open URL stderr:', stderr);
          return { output: `✓ Opened URL: ${target}` };
          
        } else {
          // Try to execute as a command
          console.log(`Executing command: ${target}`);
          const command = process.platform === 'win32' ? 
            `start "" "${target}"` : 
            target;
            
          const { stdout, stderr } = await execPromise(command);
          if (stderr) console.error('Execute command stderr:', stderr);
          return { output: `✓ Executed: ${target}` };
        }
      } catch (error) {
        console.error('Open command error:', error);
        throw new Error(`Failed to open: ${target}. Make sure the path or application exists.`);
      }
    }
  }
};

// Command execution endpoint
app.post('/api/command/execute', async (req, res) => {
  console.log('Received request body:', JSON.stringify(req.body, null, 2));
  
  const { command } = req.body;
  
  if (!command) {
    console.error('No command provided in request');
    return res.status(400).json({ 
      error: 'No command provided',
      success: false
    });
  }

  console.log('Executing command:', command);
  
  try {
    // Try to match command with allowed patterns
    let matched = false;
    let result = null;
    
    for (const [name, { pattern, handler }] of Object.entries(ALLOWED_COMMANDS)) {
      const match = command.match(pattern);
      if (match) {
        console.log(`Matched command '${name}'`);
        result = await handler(match);
        matched = true;
        break;
      }
    }

    // If no command matched, forward to AI
    if (!matched) {
      console.log('No direct command match, forwarding to AI');
      const aiResponse = await fetch('http://localhost:3001/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [{
            role: 'user',
            content: command
          }]
        }),
      });
      
      if (!aiResponse.ok) {
        throw new Error('Failed to get AI response');
      }
      
      const aiData = await aiResponse.json();
      result = { output: aiData.content };
    }

    return res.json({
      ...result,
      cwd: process.cwd(),
      success: true
    });
    
  } catch (error) {
    console.error('Command execution error:', error);
    console.error('Error stack:', error.stack);
    
    // Get more detailed error information
    const errorInfo = {
      message: error.message,
      code: error.code,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
      additionalInfo: {
        command,
        cwd: process.cwd(),
        timestamp: new Date().toISOString()
      }
    };
    
    console.error('Detailed error info:', JSON.stringify(errorInfo, null, 2));
    
    return res.status(500).json({
      error: 'Failed to execute command',
      details: process.env.NODE_ENV === 'development' ? errorInfo : undefined,
      output: `❌ Error: ${error.message}`,
      success: false,
      cwd: process.cwd()
    });
  }
});

// AI Chat Endpoint
app.post('/api/ai/chat', async (req, res) => {
  try {
    const { messages } = req.body;
    
    // Get the last user message
    const userMessage = messages[messages.length - 1]?.content || '';
    
    // Default model to use if not specified in environment variables
    const model = process.env.OLLAMA_MODEL || 'llama3.2:latest';
    
    console.log('Received request with body:', JSON.stringify(req.body, null, 2));
    
    // Validate request body
    if (!req.body || !Array.isArray(req.body.messages) || req.body.messages.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request format. Expected { messages: Array } with at least one message.'
      });
    }
    
    // Prepare the request to Ollama API
    const ollamaUrl = 'http://localhost:11434/api/chat';
    
    // Format messages for Ollama API
    const formattedMessages = [
      {
        role: 'system',
        content: 'You are JARIS, a helpful AI assistant. Provide concise and helpful responses.'
      },
      ...messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }))
    ];
    
    // Get the last message for the prompt
    const lastMessage = formattedMessages[formattedMessages.length - 1];
    
    const requestBody = {
      model: model,
      messages: formattedMessages,
      stream: false
    };

    console.log('Sending request to Ollama:', JSON.stringify(requestBody, null, 2));
    
    // Set up response headers for streaming
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    
    try {
      // Make the request to Ollama
      const ollamaResponse = await fetch(ollamaUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!ollamaResponse.ok) {
        const errorText = await ollamaResponse.text();
        console.error('Ollama API error status:', ollamaResponse.status);
        console.error('Ollama API error response:', errorText);
        throw new Error(`Ollama API error (${ollamaResponse.status}): ${errorText}`);
      }

      // Parse the response
      const responseData = await ollamaResponse.json();
      console.log('Ollama response:', JSON.stringify(responseData, null, 2));
      
      // Send the response back to the client
      return res.status(200).json({
        role: 'assistant',
        content: responseData.message?.content || 'No response content',
        model: responseData.model
      });
    } catch (error) {
      console.error('Error streaming response:', error);
      res.status(500).end();
      return;
    }
    
  } catch (error) {
    console.error('AI chat error:', error);
    console.error('Error stack:', error.stack);
    console.error('Request body:', JSON.stringify(req.body, null, 2));
    return res.status(500).json({ 
      success: false, 
      error: 'Failed to process AI chat request',
      message: error.message || 'Unknown error',
      details: process.env.NODE_ENV === 'development' ? error.stack : 'Enable development mode for detailed error'
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
