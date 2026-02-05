# 🤖 Wolf AI - Model Training Suite

This directory contains everything needed to train custom AI models for Wolf AI, including datasets, training scripts, and model deployment tools.

## 📁 Subdirectories

### 📊 `/datasets/` - Training Data
**Purpose**: High-quality datasets for training AI models

#### Files:
- **`training_dataset.jsonl`** - Main conversation dataset (102KB)
- **`training_dataset_functions.jsonl`** - Function calling dataset (2.4MB)

#### Dataset Contents:
- 💬 **Conversations** - Real user-AI interactions
- 🔧 **Function Calls** - Smart home, timer, calendar examples
- 📅 **Daily Tasks** - Planning and scheduling examples
- 🏠 **Home Automation** - Light control, device management
- 🔍 **Web Search** - Information retrieval examples

#### Data Format:
```json
{"messages": [{"role": "user", "content": "Turn on the lights"}, {"role": "assistant", "content": "I'll turn on the lights for you."}], "functions": [{"name": "control_light", "parameters": {"action": "on", "room": "living room"}}]}
```

---

### 🧪 `/scripts/` - Training & Deployment Scripts
**Purpose**: Complete pipeline for training and deploying models

#### Files:
- **`train_function_gemma.py`** - Main training script for function router
- **`generate_training_data.py`** - Create new training datasets
- **`upload_model.py`** - Deploy trained models to Hugging Face

#### Script Functions:

##### 🚀 `train_function_gemma.py`
**Purpose**: Train the FunctionGemma router model for intent classification

**What it does:**
- 🧠 Trains AI to understand user intent
- 🔗 Routes queries to correct functions (lights, timer, etc.)
- 📚 Uses conversation + function calling data
- ⚡ Optimized for GPU training

**How to Use:**
```bash
# Basic training
python model-training/scripts/train_function_gemma.py

# Training with custom parameters
python model-training/scripts/train_function_gemma.py --epochs 10 --batch-size 1

# GPU training (recommended)
python model-training/scripts/train_function_gemma.py --device cuda
```

**Training Parameters:**
- `--epochs`: Number of training cycles (default: 3)
- `--batch-size`: Training batch size (default: 1)
- `--learning-rate`: Learning rate (default: 2e-5)
- `--device`: Training device (cuda/cpu)

**What to Expect:**
```
Epoch 1/3: 100%|████████| 1000/1000 [02:30<00:00, Loss: 0.5]
Epoch 2/3: 100%|████████| 1000/1000 [02:25<00:00, Loss: 0.3]
Epoch 3/3: 100%|████████| 1000/1000 [02:20<00:00, Loss: 0.2]
✅ Training complete! Model saved to: ./merged_model
```

##### 📝 `generate_training_data.py`
**Purpose**: Generate new training datasets from conversations

**What it does:**
- 💬 Creates realistic conversation examples
- 🔧 Generates function calling examples
- 📚 Produces training data in correct format
- 🎯 Customizable for different use cases

**How to Use:**
```bash
# Generate standard dataset
python model-training/scripts/generate_training_data.py

# Generate with custom parameters
python model-training/scripts/generate_training_data.py --examples 1000 --output custom_dataset.jsonl

# Generate for specific functions
python model-training/scripts/generate_training_data.py --functions control_light,set_timer
```

**Generation Options:**
- `--examples`: Number of examples to generate (default: 500)
- `--output`: Output filename
- `--functions`: Specific functions to include
- `--include-thinking`: Add reasoning examples

---

##### 📤 `upload_model.py`
**Purpose**: Deploy trained models to Hugging Face Hub

**What it does:**
- 📤 Uploads models to Hugging Face
- 🔐 Handles authentication and permissions
- 📋 Creates model cards and documentation
- 🌍 Makes models publicly available

**How to Use:**
```bash
# Upload to Hugging Face
python model-training/scripts/upload_model.py --model-path ./merged_model --repo-name wolf-ai-router

# Upload with custom settings
python model-training/scripts/upload_model.py --model-path ./merged_model --repo-name wolf-ai-router --private
```

**Prerequisites:**
- 🗝️ Hugging Face account
- 🔑 Access token from https://huggingface.co/settings/tokens
- 📦 Trained model in `./merged_model`

---

### 📦 `/models/` - Trained Models Storage
**Purpose**: Store your custom trained models

#### Usage:
- 📁 Place trained models here
- 🔄 Backup important models
- 📋 Keep different model versions
- 🚀 Ready for deployment

---

## 🎯 Complete Training Workflow

### Step 1: Prepare Data
```bash
# Generate training data (optional)
python model-training/scripts/generate_training_data.py --examples 1000

# Review existing datasets
ls model-training/datasets/
```

### Step 2: Train Model
```bash
# Start training (GPU recommended)
python model-training/scripts/train_function_gemma.py --device cuda --epochs 5

# Monitor training progress
# Watch for decreasing loss and increasing accuracy
```

### Step 3: Test Model
```bash
# Test your trained model
python testing/model-testing/debug_router.py

# Compare with original performance
python testing/performance/speed_test.py
```

### Step 4: Deploy Model
```bash
# Upload to Hugging Face (optional)
python model-training/scripts/upload_model.py --model-path ./merged_model --repo-name my-wolf-ai-router

# Update config to use your model
# Edit config.py: HF_ROUTER_REPO = "your-username/my-wolf-ai-router"
```

---

## 🧠 Model Training Details

### What We're Training:
**FunctionGemma Router** - The AI brain that understands what you want:
- 🗣️ **Intent Classification** - "Turn on lights" → control_light
- 🔧 **Parameter Extraction** - "Turn on lights" → {action: "on", room: "living"}
- 📊 **Context Understanding** - Handles follow-up questions
- 🎯 **Accuracy Optimization** - Minimizes wrong function calls

### Training Data Types:
1. **Conversations** - Natural user requests
2. **Function Calls** - Correct function + parameters
3. **Edge Cases** - Unclear requests, multiple intents
4. **Error Handling** - What to do when requests fail

### Model Architecture:
- 🏗️ **Base Model**: FunctionGemma (fine-tuned Gemma)
- 📚 **Training Method**: Supervised fine-tuning
- 🎯 **Objective**: Minimize cross-entropy loss
- ⚡ **Optimization**: AdamW optimizer with learning rate scheduling

---

## 📊 Training Monitoring

### During Training:
```
Step 100/1000: Loss: 0.8, Accuracy: 75%
Step 200/1000: Loss: 0.6, Accuracy: 82%
Step 300/1000: Loss: 0.4, Accuracy: 89%
...
✅ Final Accuracy: 94%
```

### After Training:
```bash
# Test model accuracy
python testing/model-testing/debug_router.py

# Expected output:
✅ "Turn on lights" → control_light (confidence: 0.95)
✅ "Set timer for 5 minutes" → set_timer (confidence: 0.92)
✅ "What's the weather?" → passthrough (confidence: 0.88)
```

---

## 🛠️ Advanced Training

### Custom Datasets:
```bash
# Create your own training data
python model-training/scripts/generate_training_data.py --custom-data my_conversations.json

# Train on your data
python model-training/scripts/train_function_gemma.py --dataset my_custom_dataset.jsonl
```

### Hyperparameter Tuning:
```bash
# Try different learning rates
python model-training/scripts/train_function_gemma.py --learning-rate 1e-5

# Adjust batch size for memory constraints
python model-training/scripts/train_function_gemma.py --batch-size 2

# More epochs for better learning
python model-training/scripts/train_function_gemma.py --epochs 10
```

### GPU Requirements:
- **Minimum**: 4GB VRAM for small datasets
- **Recommended**: 8GB+ VRAM for full training
- **CPU-only**: Possible but much slower (10x+)

---

## 🐛 Troubleshooting Training

### Common Issues:
- **🔴 CUDA Out of Memory**: Reduce batch size or use CPU
- **🔴 Loss Not Decreasing**: Check data quality, adjust learning rate
- **🔴 Poor Accuracy**: More training epochs or better data
- **🔴 Model Not Saving**: Check file permissions and disk space

### Solutions:
```bash
# Memory issues
python model-training/scripts/train_function_gemma.py --batch-size 1 --device cpu

# Poor learning
python model-training/scripts/train_function_gemma.py --learning-rate 1e-4 --epochs 10

# Data issues
python model-training/scripts/generate_training_data.py --examples 2000 --high-quality
```

---

## 📈 Model Performance

### Good Training Results:
- ✅ **Accuracy**: >90% on test set
- ✅ **Loss**: <0.3 final loss
- ✅ **Inference Speed**: <100ms per query
- ✅ **Memory Usage**: <2GB VRAM

### Benchmark Comparisons:
```
Model                | Accuracy | Speed | Memory
Original Router     | 85%      | 150ms | 1.8GB
Your Custom Router  | 94%      | 120ms | 2.1GB
Perfect Router      | 98%      | 100ms | 2.5GB
```

---

This training suite gives you complete control over Wolf AI's brain! Train custom models for your specific needs and deploy them for everyone to use. 🚀🐺
