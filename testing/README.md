# 🐺 Wolf AI - Testing Suite

This directory contains all testing tools for Wolf AI to ensure quality, performance, and reliability.

## 📁 Subdirectories

### 🚀 `/performance/` - Performance & Speed Testing
**Purpose**: Test model response times, accuracy, and system performance

#### Files:
- **`speed_test.py`** - Comprehensive model performance benchmarking

#### What it tests:
- ⚡ **Response Time** - How fast models respond to queries
- 🎯 **Accuracy** - Correct answers to math, geography, science questions
- 💾 **Memory Usage** - RAM and VRAM consumption during testing
- 🔄 **Throughput** - How many queries per minute

#### How to Use:
```bash
# Run performance tests on all models
python testing/performance/speed_test.py

# Test specific model (edit MODELS list in file)
python testing/performance/speed_test.py
```

#### What to Expect:
- 📊 Performance comparison table
- ⏱️ Response time statistics
- 📈 Accuracy percentages
- 💾 System resource usage

---

### 🧪 `/unit-tests/` - Component Testing
**Purpose**: Test individual components and functions

#### Files:
- **`test_*.py`** - Individual component tests
- **`tests/`** - Complete test suite directory

#### What it tests:
- 🔧 **Core Functions** - Router, executor, TTS, STT
- 🎨 **GUI Components** - Message bubbles, timers, alarms
- 📊 **Data Management** - History, tasks, calendar
- 🔗 **API Connections** - Ollama, weather, news

#### How to Use:
```bash
# Run all unit tests
python -m pytest testing/unit-tests/

# Run specific test file
python testing/unit-tests/test_file_name.py

# Run with verbose output
python -m pytest testing/unit-tests/ -v
```

#### What to Expect:
- ✅ Pass/Fail results for each component
- 🐛 Error details if tests fail
- 📊 Coverage reports

---

### 🤖 `/model-testing/` - AI Model Specific Testing
**Purpose**: Test AI model loading, memory management, and functionality

#### Files:
- **`debug_router.py`** - Router model debugging and testing
- **`verify_unload.py`** - Model memory management testing

#### What it tests:
- 🧠 **Model Loading** - AI models load/unload correctly
- 💾 **Memory Management** - VRAM freed when models unload
- 🔄 **Router Function** - Intent classification accuracy
- 🔗 **Model Persistence** - Models stay loaded as expected

#### How to Use:
```bash
# Test router functionality
python testing/model-testing/debug_router.py

# Verify model unloading
python testing/model-testing/verify_unload.py
```

#### What to Expect:
- 📋 Router classification results
- 💾 Memory usage before/after model operations
- 🔍 Debug information for model issues

---

## 🎯 Testing Workflow

### 1. **Before Making Changes**
```bash
# Run full test suite to ensure everything works
python testing/performance/speed_test.py
python -m pytest testing/unit-tests/
python testing/model-testing/debug_router.py
```

### 2. **During Development**
```bash
# Test specific components you're working on
python testing/unit-tests/test_your_component.py
python testing/model-testing/verify_unload.py
```

### 3. **After Changes**
```bash
# Full regression testing
python testing/performance/speed_test.py
python -m pytest testing/unit-tests/
```

---

## 🐛 Troubleshooting Tests

### Common Issues:
- **🔴 Model Not Found**: Ensure model is installed with `ollama pull`
- **🔴 Memory Errors**: Close other applications or use smaller models
- **🔴 Connection Refused**: Start Ollama service with `ollama serve`

### Test Results:
- 🟢 **All Pass**: Your Wolf AI is working perfectly!
- 🟡 **Some Fail**: Check individual test output for details
- 🔴 **Many Fail**: Verify Ollama installation and model availability

---

## 📊 Understanding Test Results

### Performance Test Output:
```
Model          | Response Time | Accuracy | Memory Usage
llama3.2:3b    | 1.2s         | 95%      | 2.1GB
qwen3:1.7b      | 0.8s         | 92%      | 1.8GB
```

### Unit Test Output:
```
✅ test_router_functionality - PASSED
✅ test_tts_engine - PASSED  
❌ test_stt_microphone - FAILED (No microphone)
✅ test_calendar_manager - PASSED
```

### Model Test Output:
```
[Router] Test: "Turn on lights" -> control_light ✓
[Memory] Before: 4.2GB, After: 2.1GB ✓
[Persistence] Model stays loaded for 5 minutes ✓
```

---

## 🚀 Quick Test Commands

```bash
# Quick health check
python testing/performance/speed_test.py --quick

# Test only your current model
python testing/performance/speed_test.py --model llama3.2:3b

# Run tests with detailed output
python -m pytest testing/unit-tests/ -v -s

# Test model memory management
python testing/model-testing/verify_unload.py --detailed
```

---

## 📝 Test Customization

### Adding New Tests:
1. Create `test_new_feature.py` in `testing/unit-tests/`
2. Write test functions starting with `test_`
3. Run with `python testing/unit-tests/test_new_feature.py`

### Performance Test Customization:
- Edit `MODELS` list in `speed_test.py` to test different models
- Modify `QA_PAIRS` to test different question types
- Adjust timeouts for slower/faster systems

This testing suite ensures your Wolf AI runs reliably and performs optimally! 🐺✨
