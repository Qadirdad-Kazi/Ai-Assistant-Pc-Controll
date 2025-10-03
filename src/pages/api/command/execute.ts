import { NextApiRequest, NextApiResponse } from 'next';
import { connectToDatabase } from '@/lib/db';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  const { command } = req.body;

  if (!command) {
    return res.status(400).json({ error: 'Command is required' });
  }

  try {
    const { stdout, stderr } = await execAsync(command);
    
    if (stderr) {
      return res.status(200).json({
        success: true,
        output: stderr,
        isError: true
      });
    }
    
    return res.status(200).json({
      success: true,
      output: stdout || 'Command executed successfully',
      isError: false
    });
    
  } catch (error: any) {
    console.error('Command execution error:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to execute command',
      details: error.message,
      isError: true
    });
  }
}
