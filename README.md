# JARIS - Just A Rather Intelligent System

JARIS is an AI-powered desktop assistant that provides voice and text-based interaction, system control, and intelligent assistance. Built with React, TypeScript, and MongoDB, it offers a modern, responsive interface for managing tasks through natural language commands.

## ✨ Features

- **AI-Powered Chat**: Natural language processing for intelligent conversations
- **Voice Control**: Speech-to-text for hands-free operation
- **System Commands**: Execute system commands through natural language
- **File Operations**: Create, read, and manage files and directories
- **Responsive UI**: Modern interface built with React and Tailwind CSS
- **MongoDB Integration**: Persistent storage for chat history and user preferences

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- MongoDB Atlas account or local MongoDB instance
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/jaris-ai-assistant.git
   cd jaris-ai-assistant
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory with the following content:
   ```env
   MONGODB_URI=your_mongodb_connection_string
   NODE_ENV=development
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Open in browser**
   Visit `http://localhost:8080` in your browser

## 🛠️ Project Structure

```
jaris-ai-assistant/
├── src/
│   ├── components/     # React components
│   ├── lib/           # Utility functions and configurations
│   ├── pages/         # API routes and pages
│   └── styles/        # Global styles
├── public/            # Static files
├── .env               # Environment variables
├── package.json       # Project dependencies
└── vite.config.ts     # Vite configuration
```

## 🔧 API Endpoints

- `POST /api/ai/chat` - Process AI chat messages
- `POST /api/command/execute` - Execute system commands
- `GET /api/test-mongodb` - Test MongoDB connection

## 🤖 AI Integration

JARIS uses a flexible AI integration system that can be connected to various AI providers. The default setup includes a simple response system that can be extended with more advanced AI models.

### Extending AI Capabilities

To integrate with other AI providers (e.g., OpenAI, Anthropic):

1. Create a new API route in `src/pages/api/ai/`
2. Implement the AI provider's SDK
3. Update the chat component to use the new endpoint

## 🔒 Security Considerations

- Keep your `.env` file secure and never commit it to version control
- Use environment variables for sensitive information
- Implement proper authentication for production use
- Validate and sanitize all user inputs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Vite](https://vitejs.dev/)
- UI Components from [Shadcn UI](https://ui.shadcn.com/)
- Icons from [Lucide](https://lucide.dev/)
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/254e097e-846e-4e6d-9077-fcb024d9d475) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/features/custom-domain#custom-domain)
