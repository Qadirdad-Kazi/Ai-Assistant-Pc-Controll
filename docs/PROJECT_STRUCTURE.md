# Wolf AI - Project Structure Guide

## 📁 Organized Directory Structure

```
wolf-ai/
├── 📄 Core Application Files
│   ├── main.py                 # Application entry point
│   ├── config.py               # Central configuration
│   ├── requirements.txt        # Python dependencies
│   ├── README.md               # Project documentation
│   ├── wolf_avatar.png         # Your logo/brand image
│   ├── chat_history.db         # SQLite chat database
│   └── .gitignore              # Git ignore rules
│
├── 🧠 core/                    # Backend Logic
│   ├── router.py               # AI intent classification
│   ├── function_executor.py    # Task execution engine
│   ├── voice_assistant.py      # Voice control pipeline
│   ├── stt.py                  # Speech-to-text
│   ├── tts.py                  # Text-to-speech
│   ├── llm.py                  # AI model interface
│   ├── history.py              # Chat history management
│   ├── kasa_control.py         # Smart home control
│   ├── weather.py              # Weather service
│   ├── news.py                 # News aggregation
│   ├── tasks.py                # Task management
│   ├── calendar_manager.py     # Calendar system
│   ├── settings_store.py       # Settings persistence
│   ├── model_manager.py        # AI model loading
│   ├── model_persistence.py    # Model caching
│   └── agent/                  # Browser automation
│       ├── browser_agent.py    # Web automation
│       ├── browser_controller.py # Browser control
│       └── vlm_client.py       # Vision language model
│
├── 🎨 gui/                     # User Interface
│   ├── app.py                  # Main window
│   ├── handlers.py             # Event handlers
│   ├── styles.py               # Visual theme
│   ├── components/             # Reusable UI widgets
│   │   ├── message_bubble.py   # Chat messages
│   │   ├── voice_indicator.py  # Voice status
│   │   ├── system_monitor.py   # Performance display
│   │   ├── timer.py            # Timer widget
│   │   ├── alarm.py            # Alarm widget
│   │   ├── toast.py            # Notifications
│   │   ├── news_card.py        # News display
│   │   ├── search_indicator.py # Search status
│   │   ├── thinking_expander.py # AI thinking indicator
│   │   ├── schedule.py         # Calendar view
│   │   └── toggle_switch.py    # Custom switches
│   └── tabs/                   # Main screens
│       ├── dashboard.py       # Home screen
│       ├── chat.py             # AI chat
│       ├── planner.py          # Calendar & tasks
│       ├── briefing.py         # News feed
│       ├── home_automation.py  # Smart home
│       ├── browser.py          # Web agent
│       └── settings.py         # App settings
│
├── 📊 data/                    # Persistent Data
│   ├── calendar.db             # Calendar events
│   ├── chat_history.db         # Chat history
│   ├── tasks.db                # To-do items
│   └── test_tasks.db           # Test data
│
├── 🧪 testing/                 # All Testing Files
│   ├── performance/            # Performance & Speed Tests
│   │   └── speed_test.py       # Model performance testing
│   ├── unit-tests/             # Unit Tests
│   │   ├── test_*.py           # Individual component tests
│   │   └── tests/              # Test suite directory
│   └── model-testing/          # Model-Specific Tests
│       ├── debug_router.py     # Router debugging
│       └── verify_unload.py    # Model memory testing
│
├── 🤖 model-training/          # AI Model Development
│   ├── scripts/                # Training Scripts
│   │   ├── train_function_gemma.py    # Model training
│   │   ├── generate_training_data.py # Data generation
│   │   └── upload_model.py           # Model deployment
│   ├── datasets/               # Training Data
│   │   ├── training_dataset.jsonl    # Main dataset
│   │   └── training_dataset_functions.jsonl # Function dataset
│   └── models/                 # Trained Models (empty for now)
│
├── 🛠️ development/             # Development Tools
│   └── demo.py                 # Standalone voice assistant demo
│
├── 🔧 utilities/               # Utility Scripts
│   ├── check_icons.py          # Icon validation
│   └── icons.txt               # Icon inventory
│
├── 📋 docs/                    # Documentation
│   └── .DS_Store               # macOS system file
│
└── 📝 logs/                    # Log Files
    ├── import_error.log        # Import errors
    ├── import_error.txt        # Import errors (text)
    └── install_log.txt         # Installation log
```

## 🎯 Directory Purposes

### 📄 Core Application Files
These are the essential files needed to run Wolf AI:
- **`main.py`** - Double-click this to start the app
- **`config.py`** - All your settings and preferences
- **`requirements.txt`** - Python packages to install

### 🧠 `core/` - The Brains
All the AI logic and backend processing:
- Voice recognition and synthesis
- AI model communication
- Smart home control
- Data management

### 🎨 `gui/` - The Face
Everything you see and interact with:
- Beautiful dark theme interface
- Chat bubbles and controls
- Dashboard and settings screens

### 📊 `data/` - The Memory
Your personal data stored locally:
- Calendar events
- Chat history
- Tasks and to-dos

### 🧪 `testing/` - Quality Assurance
Three types of testing:
- **Performance** - How fast the models respond
- **Unit Tests** - Individual component testing
- **Model Testing** - AI model specific tests

### 🤖 `model-training/` - AI Development
For training custom AI models:
- Scripts to train new models
- Datasets for training
- Model deployment tools

### 🛠️ `development/` - Dev Tools
Tools for developers:
- Demo version for testing
- Development utilities

### 🔧 `utilities/` - Helper Tools
Useful utility scripts:
- Icon management
- System checks

### 📋 `docs/` & `logs/` - Documentation & Debugging
- Documentation files
- Error logs and installation records

## 🚀 Quick Start

1. **Run the app**: `python main.py`
2. **Test performance**: `python testing/performance/speed_test.py`
3. **Train models**: `python model-training/scripts/train_function_gemma.py`
4. **Development demo**: `python development/demo.py`

## 📁 File Categories Summary

| Category | Location | Purpose |
|----------|----------|---------|
| **Core App** | Root files | Essential application files |
| **AI Logic** | `core/` | Backend processing and AI |
| **User Interface** | `gui/` | Everything you see and click |
| **Your Data** | `data/` | Personal information storage |
| **Testing** | `testing/` | Quality assurance tools |
| **AI Training** | `model-training/` | Custom model development |
| **Development** | `development/` | Dev tools and demos |
| **Utilities** | `utilities/` | Helper scripts |
| **Documentation** | `docs/`, `logs/` | Reference and debugging |

This organization makes it easy to find what you need and understand how Wolf AI works! 🐺
