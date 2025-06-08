"""
AI Handler Module for Wolf AI Voice Assistant
Handles interactions with the Ollama LLM for natural language processing.
"""

import os
import json
import requests
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIModel(Enum):
    """Available AI models."""
    LLAMA2 = "llama2"
    MISTRAL = "mistral"
    CODELLAMA = "codellama"
    PHI = "phi"
    GEMMA = "gemma"
    MIXTRAL = "mixtral"

@dataclass
class AIResponse:
    """Structured response from the AI."""
    text: str
    is_command: bool = False
    command_type: Optional[str] = None
    command_args: Optional[Dict[str, Any]] = None
    confidence: float = 1.0

class AIHandler:
    """
    Handles interactions with the Ollama LLM for natural language processing.
    Supports multiple models and response formatting.
    """
    
    def __init__(self, model: AIModel = AIModel.LLAMA2, base_url: str = "http://localhost:11434"):
        """
        Initialize the AI handler.
        
        Args:
            model (AIModel): The AI model to use
            base_url (str): Base URL for the Ollama API
        """
        self.model = model
        self.base_url = base_url
        self.conversation_history = []
        self.system_prompt = self._get_default_system_prompt()
        self.max_history = 10  # Maximum number of messages to keep in history
        self.temperature = 0.7  # Controls randomness (0.0 to 1.0)
        self.max_tokens = 1000  # Maximum number of tokens to generate
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt."""
        return """You are Wolf, a helpful AI assistant. You are running on a user's computer and can help with various tasks.
        
        Your capabilities include:
        - Answering questions and providing information
        - Assisting with coding and technical tasks
        - Controlling the user's computer (opening apps, managing windows, etc.)
        - Setting reminders and managing tasks
        - And much more!
        
        Be concise, helpful, and friendly. If you're not sure about something, say so rather than making things up.
        """
    
    def set_system_prompt(self, prompt: str) -> None:
        """
        Set the system prompt that defines the AI's behavior.
        
        Args:
            prompt (str): The system prompt
        """
        self.system_prompt = prompt
    
    def set_model(self, model: AIModel) -> None:
        """
        Set the AI model to use.
        
        Args:
            model (AIModel): The AI model to use
        """
        self.model = model
    
    def set_temperature(self, temperature: float) -> None:
        """
        Set the temperature for text generation.
        
        Args:
            temperature (float): Temperature value (0.0 to 1.0)
        """
        self.temperature = max(0.0, min(1.0, temperature))
    
    def set_max_tokens(self, max_tokens: int) -> None:
        """
        Set the maximum number of tokens to generate.
        
        Args:
            max_tokens (int): Maximum number of tokens
        """
        self.max_tokens = max(10, min(4000, max_tokens))
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
    
    def _format_messages(self, user_input: str) -> List[Dict[str, str]]:
        """
        Format messages for the API request.
        
        Args:
            user_input (str): User's input text
            
        Returns:
            List[Dict[str, str]]: Formatted messages
        """
        # Add system prompt if it's the first message
        if not self.conversation_history:
            self.conversation_history.append({"role": "system", "content": self.system_prompt})
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Limit history length
        if len(self.conversation_history) > self.max_history * 2 + 1:  # *2 for user/assistant turns, +1 for system
            # Keep system prompt and the most recent messages
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-(self.max_history * 2):]
        
        return self.conversation_history
    
    def _parse_response(self, response_text: str) -> AIResponse:
        """
        Parse the AI's response text into a structured format.
        
        Args:
            response_text (str): Raw response text from the AI
            
        Returns:
            AIResponse: Structured response
        """
        # Check for commands in the response
        command_match = re.search(r'<command:(\w+)(?:\s+(.*?))?>', response_text, re.DOTALL)
        if command_match:
            command_type = command_match.group(1).lower()
            command_args = {}
            
            # Parse command arguments if any
            if command_match.group(2):
                args_text = command_match.group(2).strip()
                try:
                    # Try to parse as JSON
                    command_args = json.loads(args_text)
                except json.JSONDecodeError:
                    # If not valid JSON, treat as a simple string
                    command_args = {"query": args_text}
            
            # Clean up the response text
            clean_text = re.sub(r'<command:.*?>', '', response_text, flags=re.DOTALL).strip()
            
            return AIResponse(
                text=clean_text or f"Executing {command_type} command...",
                is_command=True,
                command_type=command_type,
                command_args=command_args
            )
        
        # No command, just return the text
        return AIResponse(text=response_text)
    
    def generate_response(self, user_input: str, stream_callback: Optional[Callable[[str], None]] = None) -> AIResponse:
        """
        Generate a response to the user's input.
        
        Args:
            user_input (str): The user's input text
            stream_callback (Callable[[str], None], optional): Callback function for streaming responses
            
        Returns:
            AIResponse: The AI's response
        """
        try:
            # Format messages for the API
            messages = self._format_messages(user_input)
            
            # Make the API request
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model.value,
                "messages": messages,
                "stream": stream_callback is not None,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            
            if stream_callback:
                # Handle streaming response
                with requests.post(url, json=payload, stream=True) as response:
                    response.raise_for_status()
                    
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            if 'message' in chunk and 'content' in chunk['message']:
                                content = chunk['message']['content']
                                full_response += content
                                stream_callback(content)
                
                # Parse the complete response
                ai_response = self._parse_response(full_response)
                
                # Add to history
                self.conversation_history.append({"role": "assistant", "content": full_response})
                
                return ai_response
            else:
                # Handle non-streaming response
                response = requests.post(url, json=payload)
                response.raise_for_status()
                
                response_data = response.json()
                response_text = response_data.get('message', {}).get('content', '')
                
                # Parse the response
                ai_response = self._parse_response(response_text)
                
                # Add to history
                self.conversation_history.append({"role": "assistant", "content": response_text})
                
                return ai_response
                
        except requests.RequestException as e:
            error_msg = f"Error communicating with Ollama API: {str(e)}"
            logger.error(error_msg)
            return AIResponse(text=error_msg, confidence=0.0)
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return AIResponse(text=error_msg, confidence=0.0)
    
    def generate_embeddings(self, text: str) -> Optional[List[float]]:
        """
        Generate embeddings for the given text.
        
        Args:
            text (str): The text to generate embeddings for
            
        Returns:
            Optional[List[float]]: The embeddings, or None if an error occurred
        """
        try:
            url = f"{self.base_url}/api/embeddings"
            payload = {
                "model": self.model.value,
                "prompt": text
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            return response.json().get('embedding')
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return None
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models from the Ollama API.
        
        Returns:
            List[Dict[str, Any]]: List of available models
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json().get('models', [])
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from the Ollama library.
        
        Args:
            model_name (str): Name of the model to pull
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(f"{self.base_url}/api/pull", json={"name": model_name})
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False

# Singleton instance
ai_handler = AIHandler()
