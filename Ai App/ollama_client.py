"""
Ollama Client Module
Handles communication with Ollama LLM for conversational AI responses
"""

import requests
import json
import os
import time
from config import Config

class OllamaClient:
    def __init__(self):
        self.config = Config()
        # Use the standard Ollama port
        self.base_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'llama3.2')
        self.timeout = 30
        
        # System prompts for different languages
        self.system_prompts = {
            'en': """You are Wolf, a helpful AI assistant. You are friendly, concise, and professional. 
            Keep your responses brief but informative. You can help with general questions, provide information, 
            and have conversations. You are integrated with a PC voice assistant system.""",
            
            'ur': """آپ Wolf ہیں، ایک مددگار AI اسسٹنٹ۔ آپ دوستانہ، مختصر، اور پیشہ ورانہ ہیں۔
            اپنے جوابات مختصر لیکن معلوماتی رکھیں۔ آپ عام سوالات میں مدد کر سکتے ہیں۔"""
        }
        
        # Static responses for common queries
        self.static_responses = {
            'en': {
                'hello': "Hello! I'm Wolf, your AI assistant. How can I help you today?",
                'hi': "Hi there! I'm Wolf, your AI assistant. What can I do for you?",
                'how are you': "I'm just a computer program, but I'm functioning perfectly! How can I assist you today?",
                'what can you do': "I can answer questions, help with tasks, set reminders, control your PC, and more! Just ask me anything.",
                'thank you': "You're welcome! Is there anything else I can help you with?",
                'goodbye': "Goodbye! Have a great day!",
                'what is your name': "I'm Wolf, your AI assistant. Nice to meet you!",
                'who made you': "I was created by a team of developers to assist you with your tasks and questions.",
                'what time is it': f"The current time is {time.strftime('%I:%M %p')}.",
                'what day is it': f"Today is {time.strftime('%A, %B %d, %Y')}.",
                'help': "I can help you with answering questions, setting reminders, controlling your PC, and more. Just tell me what you need!"
            },
            'ur': {
                'ہیلو': "ہیلو! میں ولف ہوں، آپ کا ذاتی معاون۔ میں آپ کی کس طرح مدد کر سکتا ہوں؟",
                'کیا حال ہے': "میں ایک کمپیوٹر پروگرام ہوں، لیکن میں بالکل ٹھیک کام کر رہا ہوں! آپ کیسے ہیں؟",
                'تم کیا کر سکتے ہو': "میں سوالوں کے جواب دے سکتا ہوں، یادداشتیں بنا سکتا ہوں، اور آپ کے کمپیوٹر کو کنٹرول کر سکتا ہوں۔ مجھے کچھ بھی پوچھیں!",
                'شکریہ': "آپ کا شکریہ! کیا میں آپ کی اور کسی چیز میں مدد کر سکتا ہوں؟",
                'الوداع': "خدا حافظ! آپ کا دن اچھا گزرے!",
                'تمہارا نام کیا ہے': "میرا نام ولف ہے، آپ کا ذاتی معاون۔ آپ سے مل کر خوشی ہوئی!"
            }
        }

    def get_static_response(self, user_input, language='en'):
        """
        Check if there's a static response for the user input.
        Returns the response if found, None otherwise.
        """
        user_input = user_input.lower().strip('?,.!؛؟،')
        
        # Check for exact matches first
        if user_input in self.static_responses.get(language, {}):
            return self.static_responses[language][user_input]
            
        # Check for partial matches
        for question, answer in self.static_responses.get(language, {}).items():
            if question in user_input:
                return answer
                
        return None
        
    def get_response(self, user_input, language='en'):
        """
        Get AI response, first checking static responses, then falling back to Ollama.
        
        Args:
            user_input (str): The user's input text
            language (str): Language code (default: 'en')
            
        Returns:
            str: The AI's response
        """
        # First, check if we have a static response
        static_response = self.get_static_response(user_input, language)
        if static_response:
            return static_response
            
        # If no static response, use Ollama
        system_prompt = self.system_prompts.get(language, self.system_prompts['en'])
        
        try:
            # Prepare the request data
            data = {
                "model": self.model,
                "prompt": user_input,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_ctx": 2048
                }
            }
            
            # Make the API request
            print(f"Sending request to: {self.base_url}/api/generate")
            print(f"Request data: {data}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text[:500]}..." if len(response.text) > 500 else f"Response content: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            # Handle both streaming and non-streaming responses
            if isinstance(result, dict):
                if 'response' in result:
                    return result['response'].strip()
            elif isinstance(result, list):
                # Handle streaming response
                full_response = ""
                for chunk in result:
                    if 'response' in chunk:
                        full_response += chunk['response']
                return full_response.strip() if full_response else ""
                
            print(f"Unexpected response format: {result}")
                
        except requests.exceptions.RequestException as e:
            print(f"Ollama API error: {e}")
            
        # Fallback response if API call fails
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
