import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const { messages, model = process.env.OLLAMA_MODEL || 'llama3.2:latest' } = req.body;
    
    // Get the last user message
    const userMessage = messages[messages.length - 1]?.content || '';
    
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
      details: error instanceof Error ? error.message : 'Unknown error',
      stack: process.env.NODE_ENV === 'development' ? (error as Error).stack : undefined
    });
  }
}
