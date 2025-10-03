# Testing the PC Controller

## Test Environment Setup

### Prerequisites
- Python 3.7 or higher
- All dependencies from `requirements.txt`
- `pytest` for running tests
- `pytest-cov` for test coverage (optional)
- `pytest-mock` for mocking (optional)

### Installation
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Install the package in development mode
pip install -e .
```

## Running Tests

### Running All Tests
```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=pc_controller tests/

# Generate HTML coverage report
pytest --cov=pc_controller --cov-report=html tests/
```

### Running Specific Tests
```bash
# Run a specific test file
pytest tests/test_pc_controller.py

# Run a specific test class
pytest tests/test_pc_controller.py::TestPCController

# Run a specific test method
pytest tests/test_pc_controller.py::TestPCController::test_launch_app
```

## Test Organization

### Test Files
- `tests/test_pc_controller.py`: Main test file for PCController class
- `tests/conftest.py`: Test fixtures and configuration
- `tests/mocks/`: Mock objects and helpers

### Test Categories
1. **Unit Tests**
   - Test individual methods in isolation
   - Use mocks for external dependencies
   - Focus on edge cases and error conditions

2. **Integration Tests**
   - Test interactions between components
   - Verify system behavior with real dependencies
   - Test cross-platform compatibility

3. **End-to-End Tests**
   - Test complete user workflows
   - Verify application behavior from user perspective
   - May require manual verification for some operations

## Writing Tests

### Test Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Fixtures: `*_fixture`

### Example Test Case
```python
def test_launch_app(pc_controller):
    """Test launching an application."""
    result = pc_controller.execute_command("open chrome")
    assert result['success'] is True
    assert 'Chrome' in result['message']
```

### Using Fixtures
```python
import pytest

@pytest.fixture
def pc_controller():
    """Create a PCController instance for testing."""
    controller = PCController()
    # Setup code here
    yield controller
    # Teardown code here
```

### Mocking External Dependencies
```python
def test_mouse_click(mocker, pc_controller):
    """Test mouse click with mock."""
    mock_click = mocker.patch('pyautogui.click')
    
    result = pc_controller.click_mouse_button(100, 200, 'left')
    
    assert result['success'] is True
    mock_click.assert_called_once_with(100, 200, button='left', clicks=1, interval=0.1)
```

## Test Coverage

### Generating Coverage Reports
```bash
# Generate HTML report
pytest --cov=pc_controller --cov-report=html

# Show coverage in console
pytest --cov=pc_controller
```

### Coverage Goals
- Aim for at least 80% code coverage
- Focus on testing critical paths and error conditions
- Include both positive and negative test cases

## Continuous Integration

### GitHub Actions
Example workflow (`.github/workflows/tests.yml`):
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.7', '3.8', '3.9', '3.10']
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        pytest --cov=pc_controller --cov-report=xml
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
```

## Manual Testing

### Test Cases
1. **Application Launch**
   - Test launching different applications
   - Verify error handling for non-existent apps

2. **Window Management**
   - Test minimize/maximize/close operations
   - Verify behavior with multiple windows

3. **Input Simulation**
   - Test mouse movements and clicks
   - Verify keyboard input and special keys
   - Test media controls

4. **System Operations**
   - Test screenshot functionality
   - Verify OCR text recognition
   - Test system power operations (with caution)

## Debugging Tests

### Common Issues
- **Permission Denied**: Ensure the test process has necessary permissions
- **Timing Issues**: Add small delays between operations if needed
- **Platform Differences**: Test on all target platforms

### Debugging Commands
```bash
# Run tests with debug output
pytest -v --pdb

# Run with logging
pytest --log-cli-level=DEBUG
```

## Performance Testing

### Benchmarking
```python
def test_performance(benchmark, pc_controller):
    """Benchmark mouse movement."""
    def move_mouse():
        pc_controller.move_mouse_to_coordinates(100, 100)
        pc_controller.move_mouse_to_coordinates(200, 200)
    
    benchmark(move_mouse)
```

### Performance Goals
- Mouse movements: < 100ms per operation
- Application launch: < 2 seconds for common apps
- Command execution: < 500ms for simple commands

## Security Testing

### Test Cases
1. **Input Validation**
   - Test with malicious input strings
   - Verify proper escaping of shell commands

2. **Permission Checks**
   - Test with limited user permissions
   - Verify proper error messages for unauthorized operations

3. **Data Privacy**
   - Verify sensitive data is not logged
   - Test screen reader privacy controls

## Test Maintenance

### Best Practices
- Keep tests independent and isolated
- Use meaningful test names
- Document test assumptions and requirements
- Update tests when implementation changes
- Regularly review and remove flaky tests
