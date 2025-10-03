const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
require('dotenv').config();

const app = express();
const PORT = 3001;

// Middleware - Enable CORS for all routes
app.use(cors());
app.use(bodyParser.json());

// Simple test route
app.get('/api/test', (req, res) => {
  console.log('Test endpoint hit');
  res.json({ status: 'Server is running', time: new Date().toISOString() });
});

// AI Chat Endpoint
app.post('/api/ai/chat', async (req, res) => {
  try {
    const { messages } = req.body;
    
    // Get the last user message
    const userMessage = messages[messages.length - 1]?.content || '';
    
    // Default model to use if not specified in environment variables
    const model = process.env.OLLAMA_MODEL || 'llama3';
    
    // Call the local Ollama API
    const response = await fetch('http://localhost:11434/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: 'system',
            content: 'You are JARIS, a helpful AI assistant. Provide concise and helpful responses.'
          },
          ...messages.map(msg => ({
            role: msg.role,
            content: msg.content
          }))
        ],
        stream: false,
        options: {
          temperature: 0.7,
          top_p: 0.9,
        }
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Ollama API error:', error);
      throw new Error(`Ollama API error: ${error}`);
    }

    const data = await response.json();
    
    return res.status(200).json({
      role: 'assistant',
      content: data.message?.content || 'I apologize, but I encountered an error processing your request.'
    });
    
  } catch (error) {
    console.error('AI chat error:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Failed to process AI chat request',
      details: error.message || 'Unknown error',
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
