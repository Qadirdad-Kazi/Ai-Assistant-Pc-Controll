import { NextApiRequest, NextApiResponse } from 'next';
import { connectToDatabase } from '@/lib/db';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const { db } = await connectToDatabase();
    
    // Test the connection by listing all collections
    const collections = await db.listCollections().toArray();
    
    return res.status(200).json({ 
      success: true, 
      collections: collections.map(c => c.name)
    });
    
  } catch (error) {
    console.error('MongoDB connection error:', error);
    return res.status(500).json({ 
      success: false, 
      error: 'Failed to connect to MongoDB',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}
