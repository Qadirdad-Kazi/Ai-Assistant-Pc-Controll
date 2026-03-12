# 🧪 Wolf AI 2.0 Ultimate Enhancement Testing Suite

This comprehensive testing suite covers all the cutting-edge features of Wolf AI 2.0, including Vision Agent UI grounding, Neural Sonic TTS, Memory Recall, Deep Research, and Bug Watcher capabilities.

## 📋 Test Suite Overview

### Core Test Files

| Test File | Module | Test Types | Coverage |
|-----------|--------|------------|----------|
| `test_vision_agent.py` | Vision Agent (OmniParser) | Unit, Integration | UI grounding, screen analysis |
| `test_neural_sonic.py` | Neural Sonic (Kokoro TTS) | Unit, Integration | Speech synthesis, voice control |
| `test_memory_recall.py` | Memory System | Unit, Integration | History browsing, preferences |
| `test_deep_research.py` | Deep Research (Crawl4AI) | Unit, Integration | Web intelligence, content extraction |
| `test_bug_watcher.py` | Bug Watcher (OCR) | Unit, Integration | Proactive error detection |
| `test_integration_comprehensive.py` | Multi-Module | Integration | End-to-end workflows |
| `test_performance_stress.py` | All Modules | Performance, Stress | Load testing, resource management |

### Advanced Test Runner

| Feature | Description |
|---------|-------------|
| **Enhanced Test Runner** | `test_runner.py` with comprehensive reporting |
| **HTML Reports** | Visual test reports with metrics and recommendations |
| **Performance Monitoring** | Real-time CPU, memory, and performance tracking |
| **Continuous Monitoring** | Automated health checks and monitoring |
| **Benchmarking** | Performance benchmarks for all modules |

## 🚀 Quick Start

### Basic Test Execution

```bash
# Run all tests
python tests/test_runner.py

# Run specific module tests
python tests/test_runner.py --suite vision
python tests/test_runner.py --suite tts
python tests/test_runner.py --suite memory
python tests/test_runner.py --suite research
python tests/test_runner.py --suite bugwatcher

# Include integration tests
python tests/test_runner.py --integration

# Run performance benchmarks
python tests/test_runner.py --performance

# Start continuous monitoring
python tests/test_runner.py --continuous
```

### Advanced Test Options

```bash
# Filter by test type
python tests/test_runner.py --type unit
python tests/test_runner.py --type integration
python tests/test_runner.py --type performance

# Custom report location
python tests/test_runner.py --report my_test_report.json

# Skip health check (faster execution)
python tests/test_runner.py --skip-health
```

### PyTest Direct Execution

```bash
# Run individual test files
python -m pytest tests/test_vision_agent.py -v
python -m pytest tests/test_integration_comprehensive.py -v

# Run with markers
python -m pytest tests/ -m unit -v
python -m pytest tests/ -m integration -v
python -m pytest tests/ -m performance -v

# Run stress tests
python -m pytest tests/test_performance_stress.py -v -s
```

## 📊 Test Categories

### 🏗️ Unit Tests
- **Purpose**: Test individual module functionality
- **Markers**: `@pytest.mark.unit`
- **Speed**: Fast (< 5 seconds per module)
- **Dependencies**: Mocked external services

### 🔗 Integration Tests
- **Purpose**: Test module interactions and workflows
- **Markers**: `@pytest.mark.integration`
- **Speed**: Medium (5-30 seconds)
- **Dependencies**: May require external services

### ⚡ Performance Tests
- **Purpose**: Benchmark and performance validation
- **Markers**: `@pytest.mark.performance`, `@pytest.mark.slow`
- **Speed**: Slow (30+ seconds)
- **Resources**: CPU, memory intensive

### 🐛 Stress Tests
- **Purpose**: System stability under load
- **Markers**: `@pytest.mark.stress`
- **Speed**: Very slow (1+ minutes)
- **Resources**: High CPU, memory usage

## 🎯 Module-Specific Testing

### Vision Agent (OmniParser Integration)

**Test Coverage:**
- Screen capture and base64 encoding
- UI element detection and parsing
- Click action grounding and execution
- Screen description generation
- Error handling and connection testing
- Confidence filtering and batch processing

**Key Test Scenarios:**
```bash
# Run vision tests
python -m pytest tests/test_vision_agent.py::TestVisionAgent -v

# Integration tests
python -m pytest tests/test_vision_agent.py::TestVisionIntegration -v -s
```

### Neural Sonic (Kokoro TTS)

**Test Coverage:**
- Model initialization and loading
- Text-to-speech synthesis
- Audio quality validation
- Voice variations and speed control
- Concurrent synthesis handling
- Integration with main TTS system

**Key Test Scenarios:**
```bash
# Run TTS tests
python -m pytest tests/test_neural_sonic.py::TestNeuralSonic -v

# Real synthesis tests (requires model)
python -m pytest tests/test_neural_sonic.py::TestNeuralSonicIntegration -v -s
```

### Memory Recall System

**Test Coverage:**
- Memory storage and retrieval
- Preference learning and recall
- Search functionality and tagging
- Context-aware memory operations
- Cross-session persistence
- Concurrent memory operations

**Key Test Scenarios:**
```bash
# Run memory tests
python -m pytest tests/test_memory_recall.py::TestMemoryRecall -v

# Real database tests
python -m pytest tests/test_memory_recall.py::TestMemoryRecallIntegration -v -s
```

### Deep Research (Crawl4AI)

**Test Coverage:**
- Web search functionality
- URL content scraping
- JavaScript rendering
- Overlay bypass techniques
- Content extraction and cleaning
- Research report generation

**Key Test Scenarios:**
```bash
# Run research tests
python -m pytest tests/test_deep_research.py::TestDeepResearch -v

# Live web tests
python -m pytest tests/test_deep_research.py::TestDeepResearchIntegration -v -s
```

### Bug Watcher (Proactive OCR)

**Test Coverage:**
- Screen capture and OCR processing
- Error pattern matching
- Confidence scoring
- False positive filtering
- Vision agent confirmation
- Continuous monitoring

**Key Test Scenarios:**
```bash
# Run bug watcher tests
python -m pytest tests/test_bug_watcher.py::TestBugWatcher -v

# Real OCR tests
python -m pytest tests/test_bug_watcher.py::TestBugWatcherIntegration -v -s
```

## 📈 Performance Monitoring

### Metrics Tracked

- **CPU Usage**: Peak and average CPU utilization
- **Memory Usage**: Peak memory consumption and leaks
- **Response Time**: Operation latency and throughput
- **Concurrency**: Performance under parallel load
- **Resource Cleanup**: File descriptor and memory management

### Performance Benchmarks

```bash
# Run performance benchmarks
python tests/test_runner.py --performance

# Detailed stress testing
python -m pytest tests/test_performance_stress.py::TestPerformanceStress -v -s

# Sustained load testing
python -m pytest tests/test_performance_stress.py::TestLoadTesting -v -s
```

## 🔧 Configuration

### Test Configuration (`tests/conftest.py`)

```python
# Test markers configuration
markers = [
    unit: Unit tests (fast, no external dependencies),
    integration: Integration tests (requires external services),
    slow: Slow running tests,
    vision: Tests requiring vision components,
    tts: Tests requiring TTS components,
    memory: Tests requiring memory/database,
    research: Tests requiring web access,
    bugwatcher: Tests requiring OCR/screen capture
]
```

### PyTest Configuration (`tests/pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers --color=yes
asyncio_mode = auto
timeout = 300
```

## 📊 Reporting

### Report Types

1. **JSON Reports**: Machine-readable detailed results
2. **HTML Reports**: Visual dashboard with charts
3. **Console Reports**: Real-time progress and summaries
4. **Performance Reports**: Resource usage and benchmarks

### Report Locations

```
tests/
├── reports/
│   ├── wolf_ai_test_report.json     # Main report
│   ├── wolf_ai_test_report.html     # Visual dashboard
│   ├── performance_benchmarks.json  # Performance data
│   └── continuous_monitoring.json   # Health monitoring
```

### Report Analysis

The test runner provides:
- **Health Assessment**: Overall system readiness score
- **Performance Metrics**: CPU, memory, and timing data
- **Coverage Analysis**: Module and feature coverage
- **Recommendations**: Actionable improvement suggestions
- **Trend Analysis**: Performance over time

## 🏥 Health Monitoring

### System Health Checks

- **Python Version**: 3.10+ requirement validation
- **Dependencies**: Required packages availability
- **External Services**: Ollama, OmniParser connectivity
- **Resource Availability**: Memory, disk space checks

### Continuous Monitoring

```bash
# Start continuous monitoring (5-minute intervals)
python tests/test_runner.py --continuous

# Custom monitoring interval (in seconds)
python tests/test_runner.py --continuous --interval 300
```

## 🐛 Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install pytest pytest-asyncio psutil
   ```

2. **External Services Not Running**
   - Start Ollama: `ollama serve`
   - Start OmniParser: `python engines/omni_parser/omni_server.py`

3. **Permission Issues**
   ```bash
   # On Windows, run as administrator for screen capture tests
   # On Linux/macOS, ensure display access
   ```

4. **Memory Issues**
   ```bash
   # Reduce concurrent operations
   python -m pytest tests/ -m "not performance" -v
   ```

### Debug Mode

```bash
# Enable verbose output
python -m pytest tests/ -v -s --tb=long

# Stop on first failure
python -m pytest tests/ -x --tb=short

# Run specific failing test
python -m pytest tests/test_vision_agent.py::TestVisionAgent::test_screen_capture -v -s
```

## 📝 Best Practices

### Test Development

1. **Use Fixtures**: Leverage `conftest.py` for shared setup
2. **Mock External Services**: Use mocks for consistent testing
3. **Mark Tests Appropriately**: Use pytest markers for categorization
4. **Handle Async**: Use `@pytest.mark.asyncio` for async tests
5. **Clean Resources**: Ensure proper cleanup in tests

### Continuous Integration

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    python tests/test_runner.py --type unit --skip-health
    
- name: Run Integration Tests
  run: |
    python tests/test_runner.py --integration --type integration
    
- name: Performance Benchmarks
  run: |
    python tests/test_runner.py --performance
```

## 🎯 Test Coverage Goals

### Target Coverage

| Module | Unit Tests | Integration Tests | Performance Tests |
|--------|-----------|------------------|------------------|
| Vision Agent | ✅ 95% | ✅ 80% | ✅ 70% |
| Neural Sonic | ✅ 90% | ✅ 75% | ✅ 65% |
| Memory System | ✅ 95% | ✅ 85% | ✅ 70% |
| Deep Research | ✅ 85% | ✅ 70% | ✅ 60% |
| Bug Watcher | ✅ 90% | ✅ 80% | ✅ 65% |

### Coverage Reports

```bash
# Generate coverage report
pip install pytest-cov
python -m pytest tests/ --cov=core --cov-report=html
```

## 🚀 Future Enhancements

### Planned Features

- **Visual Regression Testing**: UI comparison tests
- **Load Testing Infrastructure**: Scalability testing
- **Automated Performance Baselines**: Performance regression detection
- **Cross-Platform Testing**: Windows, Linux, macOS compatibility
- **API Testing**: REST API endpoint testing
- **Security Testing**: Vulnerability scanning

### Contributing

When adding new tests:
1. Follow existing naming conventions
2. Add appropriate pytest markers
3. Update documentation
4. Include performance considerations
5. Add integration tests where applicable

---

## 📞 Support

For testing questions or issues:
1. Check this README first
2. Review test file docstrings
3. Enable verbose output for debugging
4. Check the troubleshooting section
5. Review the main project documentation

**Happy Testing! 🧪✨**
