import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

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
