"""
Ollama Client Module
Handles communication with Ollama LLM for conversational AI responses
"""

import requests
import json
import os
from config import Config

class OllamaClient:
    def __init__(self):
        self.config = Config()
        self.base_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'llama2')
        self.timeout = 30
        
        # System prompts for different languages
        self.system_prompts = {
            'en': """You are Wolf, a helpful AI assistant. You are friendly, concise, and professional. 
            Keep your responses brief but informative. You can help with general questions, provide information, 
            and have conversations. You are integrated with a PC voice assistant system.""",
            
            'ur': """آپ Wolf ہیں، ایک مددگار AI اسسٹنٹ۔ آپ دوستانہ، مختصر، اور پیشہ ورانہ ہیں۔
            اپنے جوابات مختصر لیکن معلوماتی رکھیں۔ آپ عام سوالات میں مدد کر سکتے ہیں۔"""
        }

    def get_response(self, user_input, language='en'):
        """
        Get AI response from Ollama
        """
        try:
            # Check if Ollama is available
            if not self.is_ollama_available():
                return self.get_fallback_response(user_input, language)
            
            # Prepare the prompt
            system_prompt = self.system_prompts.get(language, self.system_prompts['en'])
            
            # Create the request payload
            payload = {
                "model": self.model,
                "prompt": f"System: {system_prompt}\n\nUser: {user_input}\n\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 200,
                    "stop": ["User:", "System:"]
                }
            }
            
            # Make the request
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                
                if ai_response:
                    return ai_response
                else:
                    return self.get_fallback_response(user_input, language)
            else:
                print(f"Ollama API error: {response.status_code}")
                return self.get_fallback_response(user_input, language)
                
        except requests.exceptions.ConnectionError:
            print("Could not connect to Ollama")
            return self.get_fallback_response(user_input, language)
        except requests.exceptions.Timeout:
            print("Ollama request timed out")
            return self.get_fallback_response(user_input, language)
        except Exception as e:
            print(f"Ollama client error: {str(e)}")
            return self.get_fallback_response(user_input, language)

    def is_ollama_available(self):
        """
        Check if Ollama service is available
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_fallback_response(self, user_input, language='en'):
        """
        Provide fallback responses when Ollama is not available
        """
        user_input_lower = user_input.lower()
        
        # Language-specific fallback responses
        if language == 'ur':
            fallbacks = {
                'hello': 'السلام علیکم! میں Wolf ہوں۔ آپ کی کیا مدد کر سکتا ہوں؟',
                'how are you': 'میں ٹھیک ہوں، شکریہ! آپ کیسے ہیں؟',
                'time': 'مجھ سے وقت پوچھنے کے لیے "what time is it" کہیں۔',
                'weather': 'معذرت، میں فی الوقت موسمی معلومات فراہم نہیں کر سکتا۔',
                'joke': 'ایک مزاحیہ کہانی: کمپیوٹر کیوں ٹھنڈا رہتا ہے؟ کیونکہ یہ اپنی windows کھلی رکھتا ہے!',
                'default': 'معذرت، AI سروس دستیاب نہیں ہے۔ کرپیا دوبارہ کوشش کریں۔'
            }
        else:
            fallbacks = {
                'hello': "Hello! I'm Wolf, your AI assistant. How can I help you today?",
                'how are you': "I'm doing well, thank you! How are you?",
                'time': 'To get the current time, say "what time is it".',
                'weather': "I'm sorry, I can't provide weather information at the moment.",
                'joke': "Here's a joke: Why do computers stay cool? Because they have great Windows!",
                'help': "I can help you control your PC, answer questions, and have conversations. Try asking me to open apps, take screenshots, or just chat!",
                'default': "I'm sorry, the AI service is currently unavailable. Please try again later."
            }
        
        # Match user input to appropriate response
        for key, response in fallbacks.items():
            if key in user_input_lower:
                return response
        
        # Default response
        return fallbacks['default']

    def test_connection(self):
        """
        Test connection to Ollama and return status
        """
        try:
            if self.is_ollama_available():
                # Try to get a simple response
                test_response = self.get_response("Hello, can you hear me?")
                return {
                    'success': True,
                    'message': 'Ollama connection successful',
                    'response': test_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Ollama service not available'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}'
            }

# Test the Ollama client
if __name__ == "__main__":
    client = OllamaClient()
    
    # Test connection
    print("Testing Ollama connection...")
    result = client.test_connection()
    print(f"Connection test: {result}")
    
    if result['success']:
        # Test some queries
        test_queries = [
            "Hello, what's your name?",
            "Tell me a joke",
            "What can you help me with?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            response = client.get_response(query)
            print(f"Response: {response}")
    else:
        print("Ollama not available, testing fallback responses...")
        fallback_response = client.get_fallback_response("Hello")
        print(f"Fallback response: {fallback_response}")
