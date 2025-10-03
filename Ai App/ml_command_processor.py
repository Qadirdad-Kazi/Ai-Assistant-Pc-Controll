"""
Machine Learning Command Processor for AI Assistant

This module provides functionality to learn from user commands and predict actions
using machine learning techniques.
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLCommandProcessor:
    """Machine Learning based command processor for the AI Assistant."""
    
    def __init__(self, model_path: str = 'ml_models/command_classifier.joblib'):
        """Initialize the ML Command Processor.
        
        Args:
            model_path: Path to save/load the trained model
        """
        self.model_path = model_path
        self.training_data_path = 'data/command_training_data.json'
        self.vectorizer = TfidfVectorizer(
            lowercase=True, 
            stop_words='english',
            ngram_range=(1, 2),
            max_features=1000
        )
        self.model = Pipeline([
            ('tfidf', self.vectorizer),
            ('clf', RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced'
            ))
        ])
        self.commands = {}  # Maps command IDs to command details
        self._load_training_data()
        self._load_model()
    
    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        try:
            # Ensure parent directories exist
            os.makedirs(os.path.dirname(os.path.abspath(self.training_data_path)), exist_ok=True)
            os.makedirs(os.path.dirname(os.path.abspath(self.model_path)), exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            return False
    
    def _load_training_data(self) -> None:
        """Load training data from file if it exists."""
        if not self._ensure_data_dir():
            logger.error("Failed to create data directories")
            
        self.training_data = {
            'texts': [],
            'labels': [],
            'commands': {}
        }
        
        try:
            if os.path.exists(self.training_data_path):
                with open(self.training_data_path, 'r') as f:
                    data = json.load(f)
                    self.training_data = {
                        'texts': data.get('texts', []),
                        'labels': data.get('labels', []),
                        'commands': data.get('commands', {})
                    }
                    self.commands = self.training_data['commands']
                    logger.info(f"Loaded {len(self.training_data['texts'])} training examples")
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
    
    def _save_training_data(self) -> bool:
        """Save training data to file.
        
        Returns:
            bool: True if save was successful, False otherwise
        """
        if not self._ensure_data_dir():
            logger.error("Failed to create data directories")
            return False
            
        try:
            with open(self.training_data_path, 'w') as f:
                json.dump({
                    'texts': self.training_data['texts'],
                    'labels': self.training_data['labels'],
                    'commands': self.commands
                }, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving training data: {e}")
            return False
    
    def _load_model(self) -> None:
        """Load a pre-trained model if it exists."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                # Update the vectorizer reference
                self.vectorizer = self.model.named_steps['tfidf']
            except Exception as e:
                logger.error(f"Error loading model: {e}")
    
    def save_model(self) -> None:
        """Save the current model to disk."""
        try:
            joblib.dump(self.model, self.model_path)
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def add_training_example(self, text: str, command_id: str, command_details: Dict[str, Any]) -> bool:
        """Add a new training example.
        
        Args:
            text: The input text/command
            command_id: Unique identifier for the command
            command_details: Details about the command to execute
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            # Add to training data
            self.training_data['texts'].append(text.lower())
            self.training_data['labels'].append(command_id)
            
            # Update command details if not already present
            if command_id not in self.commands:
                self.commands[command_id] = {
                    'details': command_details,
                    'created_at': datetime.now().isoformat(),
                    'examples': []
                }
            
            # Add this example to the command's examples
            self.commands[command_id]['examples'].append({
                'text': text,
                'added_at': datetime.now().isoformat()
            })
            
            # Save the updated training data
            self._save_training_data()
            return True
        except Exception as e:
            logger.error(f"Error adding training example: {e}")
            return False
    
    def train(self) -> Dict[str, Any]:
        """Train the model on the current training data.
        
        Returns:
            Dict containing training metrics
        """
        if not self.training_data['texts']:
            return {'status': 'error', 'message': 'No training data available'}
        
        try:
            # Convert to numpy arrays
            X = np.array(self.training_data['texts'])
            y = np.array(self.training_data['labels'])
            
            # If we have very few examples, do a simple train/test split
            if len(np.unique(y)) < 2 or len(y) < 5:
                # Simple training without test split for very small datasets
                self.model.fit(X, y)
                accuracy = 1.0  # Assume 100% accuracy for training data
                
                return {
                    'status': 'success',
                    'accuracy': accuracy,
                    'train_samples': len(X),
                    'test_samples': 0,
                    'message': 'Trained on all available data (small dataset)'
                }
            
            # For larger datasets, do a proper train/test split
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, stratify=y
                )
                
                # Train the model
                self.model.fit(X_train, y_train)
                
                # Evaluate on test set
                y_pred = self.model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                
                # Save the trained model
                self.save_model()
                
                return {
                    'status': 'success',
                    'accuracy': accuracy,
                    'train_samples': len(X_train),
                    'test_samples': len(X_test)
                }
                
            except ValueError as ve:
                # Fallback to simple training if stratification fails
                logger.warning(f"Stratified split failed, using simple split: {ve}")
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
                
                self.model.fit(X_train, y_train)
                y_pred = self.model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                
                self.save_model()
                
                return {
                    'status': 'success',
                    'accuracy': accuracy,
                    'train_samples': len(X_train),
                    'test_samples': len(X_test),
                    'warning': 'Used simple train/test split (stratification failed)'
                }
                
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def predict_command(self, text: str, threshold: float = 0.5) -> Dict[str, Any]:
        """Predict the most likely command for the given text.
        
        Args:
            text: Input text/command
            threshold: Confidence threshold for prediction (0-1)
            
        Returns:
            Dict containing prediction results
        """
        if not hasattr(self, 'model') or not self.training_data['texts']:
            return {
                'status': 'error',
                'message': 'Model not trained or no training data available'
            }
        
        try:
            # Get prediction probabilities
            probas = self.model.predict_proba([text.lower()])[0]
            max_prob = np.max(probas)
            predicted_idx = np.argmax(probas)
            predicted_label = self.model.classes_[predicted_idx]
            
            # Check if confidence is above threshold
            if max_prob < threshold:
                return {
                    'status': 'low_confidence',
                    'confidence': float(max_prob),
                    'message': f'No confident prediction (confidence: {max_prob:.2f} < {threshold})'
                }
            
            # Get command details
            command_details = self.commands.get(predicted_label, {})
            
            return {
                'status': 'success',
                'command_id': predicted_label,
                'command_details': command_details.get('details', {}),
                'confidence': float(max_prob),
                'all_predictions': [
                    {
                        'command_id': label,
                        'confidence': float(prob),
                        'details': self.commands.get(label, {}).get('details', {})
                    }
                    for label, prob in zip(self.model.classes_, probas)
                ]
            }
        except Exception as e:
            logger.error(f"Error predicting command: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_command_details(self, command_id: str) -> Dict[str, Any]:
        """Get details for a specific command.
        
        Args:
            command_id: ID of the command
            
        Returns:
            Dict containing command details or None if not found
        """
        return self.commands.get(command_id, {})
    
    def list_commands(self) -> List[Dict[str, Any]]:
        """Get a list of all learned commands.
        
        Returns:
            List of command details
        """
        return [
            {'command_id': cmd_id, **details}
            for cmd_id, details in self.commands.items()
        ]
    
    def delete_command(self, command_id: str) -> bool:
        """Delete a command and its training examples.
        
        Args:
            command_id: ID of the command to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        if command_id not in self.commands:
            return False
        
        try:
            # Remove command from commands dict
            del self.commands[command_id]
            
            # Remove training examples for this command
            indices_to_keep = [
                i for i, label in enumerate(self.training_data['labels'])
                if label != command_id
            ]
            
            self.training_data['texts'] = [
                self.training_data['texts'][i] for i in indices_to_keep
            ]
            self.training_data['labels'] = [
                self.training_data['labels'][i] for i in indices_to_keep
            ]
            
            # Save the updated training data
            self._save_training_data()
            
            # Retrain the model if there's still data
            if self.training_data['texts']:
                self.train()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting command: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize the command processor
    processor = MLCommandProcessor()
    
    # Add some training examples
    processor.add_training_example(
        text="open chrome browser",
        command_id="open_chrome",
        command_details={
            "action": "run_command",
            "command": "open -a \"Google Chrome\"",
            "description": "Opens Google Chrome browser"
        }
    )
    
    processor.add_training_example(
        text="launch chrome",
        command_id="open_chrome",
        command_details={
            "action": "run_command",
            "command": "open -a \"Google Chrome\"",
            "description": "Opens Google Chrome browser"
        }
    )
    
    processor.add_training_example(
        text="open terminal",
        command_id="open_terminal",
        command_details={
            "action": "run_command",
            "command": "open -a Terminal .",
            "description": "Opens a new Terminal window"
        }
    )
    
    # Train the model
    training_result = processor.train()
    print(f"Training completed with accuracy: {training_result.get('accuracy', 0):.2f}")
    
    # Test prediction
    test_phrases = ["open chrome", "launch terminal app", "start chrome browser"]
    
    for phrase in test_phrases:
        prediction = processor.predict_command(phrase)
        print(f"\nPhrase: {phrase}")
        print(f"Prediction: {prediction}")
    
    # List all learned commands
    print("\nLearned commands:")
    for cmd in processor.list_commands():
        print(f"- {cmd['command_id']}: {cmd.get('details', {}).get('description', 'No description')}")
