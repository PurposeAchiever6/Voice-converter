# Voice Converter - Project Structure

This document outlines the organized structure of the Voice Converter project.

## Root Directory Structure

```
Voice-converter/
├── README.md                 # Main project documentation
├── .gitignore               # Git ignore rules (excludes tests, logs, etc.)
├── backend/                 # Backend API server
├── frontend/                # React frontend application
├── docs/                    # Project documentation
├── tests/                   # Root-level integration tests
├── examples/                # Usage examples and demos
├── scripts/                 # Utility scripts
└── logs/                    # Application logs (gitignored)
```

## Backend Structure

```
backend/
├── app/                     # Main application code
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point
│   ├── models/             # Data models
│   │   ├── __init__.py
│   │   └── audio.py
│   ├── services/           # Business logic services
│   │   ├── __init__.py
│   │   ├── audio_processor.py
│   │   ├── elevenlabs_service.py
│   │   ├── gladia_service.py
│   │   ├── sentence_processor.py
│   │   └── storage_service.py
│   └── utils/              # Utility functions
│       ├── __init__.py
│       ├── config.py
│       └── logger.py
├── docs/                   # Backend-specific documentation
│   ├── CONTINUOUS_MODE_SOLUTION.md
│   ├── CONTINUOUS_NO_GAPS_SOLUTION.md
│   ├── CONTINUOUS_WITH_SPACES_API.md
│   └── TIMESTAMP_PROCESSING_GUIDE.md
├── examples/               # Backend examples and demos
│   ├── analyze_real_output.py
│   ├── demonstrate_api_output.py
│   └── generate_output_example.py
├── tests/                  # Backend unit and integration tests
├── scripts/                # Backend utility scripts
├── logs/                   # Backend logs (gitignored)
├── outputs/                # Generated audio files (gitignored)
├── uploads/                # Uploaded files (gitignored)
├── .env.example           # Environment variables template
├── .gitignore             # Backend-specific git ignore
├── requirements.txt       # Python dependencies
└── start.py              # Backend server startup script
```

## Frontend Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── App.js              # Main React component
│   ├── index.js            # React entry point
│   ├── index.css           # Global styles
│   ├── components/         # React components
│   │   ├── FileUpload.js
│   │   └── ProgressTracker.js
│   └── services/           # API and service layers
│       └── api.js
├── .env.example           # Frontend environment template
├── .gitignore             # Frontend-specific git ignore
├── package.json           # Node.js dependencies
├── package-lock.json      # Locked dependency versions
├── postcss.config.js      # PostCSS configuration
└── tailwind.config.js     # Tailwind CSS configuration
```

## Documentation Structure

```
docs/
├── PROJECT_STRUCTURE.md   # This file
└── SETUP_GUIDE.md         # Setup and installation guide
```

## Test Organization

- **Root tests/**: Integration tests that test the entire system
- **backend/tests/**: Backend-specific unit and API tests
- **All test files**: Excluded from git repository via .gitignore

## Key Features of This Structure

1. **Clear Separation**: Frontend, backend, and documentation are clearly separated
2. **Test Isolation**: All test files are organized in dedicated directories and excluded from git
3. **Documentation**: Centralized documentation with backend-specific docs in backend/docs/
4. **Examples**: Demo and example code separated from production code
5. **Environment Management**: Template .env files for easy setup
6. **Logging**: Dedicated log directories (excluded from git)
7. **Clean Git History**: .gitignore configured to exclude temporary files, tests, and logs

## Development Workflow

1. **Production Code**: Located in `backend/app/` and `frontend/src/`
2. **Testing**: Use files in `tests/` and `backend/tests/` directories
3. **Documentation**: Update files in `docs/` and `backend/docs/`
4. **Examples**: Reference files in `examples/` and `backend/examples/`

This structure ensures a clean, professional codebase that separates concerns and maintains a clear development workflow.
