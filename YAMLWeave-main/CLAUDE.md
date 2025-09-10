# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YAMLWeave is a C code automatic instrumentation tool that supports two working modes:
1. **Traditional mode**: Extracts stub code directly from comments  
2. **Separation mode**: Loads stub code from YAML configuration files (anchors separated from stub code)

The tool is written in Python with a Tkinter GUI and can be packaged as a standalone executable.

## Development Commands

### Running the Application
```bash
# Run in development mode
python code/main.py

# Run specific tests (no formal test framework - uses example files)
python code/main.py [project_directory] --yaml [yaml_config_file]
```

### Building/Packaging
```bash
# Build standalone executable
python scripts/build_exe.py

# This will:
# - Check dependencies (PyInstaller, PyYAML)
# - Validate Python file syntax
# - Create timestamped executable in project root
# - Include all necessary dependencies and data files
```

### Dependencies
Install dependencies from requirements.txt:
```bash
pip install -r requirements.txt

# Core dependencies:
# - PyYAML>=6.0 (YAML configuration parsing)
# - chardet>=5.0 (file encoding detection)
# - python-docx>=0.8.11 (patent document processing)
# - markdown>=3.4.1 (documentation)
# - beautifulsoup4>=4.11.1 (HTML processing)
```

## Architecture Overview

The codebase follows a modular architecture with clear separation of concerns:

### Core Structure
```
YAMLWeave/
├── code/                    # Main application code
│   ├── main.py             # Application entry point with GUI/CLI support
│   ├── core/               # Core processing logic
│   │   ├── stub_processor.py  # Main processing orchestrator
│   │   ├── stub_parser.py     # C code parsing and anchor detection
│   │   └── utils.py           # File operations and encoding handling
│   ├── handlers/           # Specialized processors
│   │   ├── yaml_handler.py    # YAML configuration management
│   │   └── comment_handler.py # Code insertion logic
│   ├── ui/                 # User interface
│   │   ├── app_ui.py          # Main GUI implementation
│   │   ├── app_controller.py  # UI-logic connector with adapter pattern
│   │   └── rounded_progressbar.py  # Custom progress bar widget
│   └── utils/              # Utilities and infrastructure
│       ├── logger.py          # Logging system with UI integration
│       ├── file_utils.py      # Advanced file operations
│       ├── config.py          # Configuration management
│       └── exceptions.py      # Custom exception definitions
├── scripts/                # Build and utility scripts
│   └── build_exe.py        # PyInstaller packaging script
└── requirements.txt        # Python dependencies
```

### Key Design Patterns

1. **Adapter Pattern**: `StubProcessorAdapter` in app_controller.py ensures compatibility across different processor versions

2. **Separation of Concerns**: 
   - Core logic (stub_processor.py) orchestrates the overall process
   - Specialized handlers manage YAML and comment processing
   - UI components are cleanly separated from business logic

3. **Error Recovery**: Multiple fallback mechanisms throughout the codebase handle missing components or import failures

4. **Dual Mode Architecture**: Supports both traditional comment-based stubbing and modern YAML-based anchor/stub separation

## Working with the Codebase

### Adding New Features
- Core processing logic goes in `code/core/`
- UI enhancements go in `code/ui/`
- New file format handlers go in `code/handlers/`
- Utilities and infrastructure go in `code/utils/`

### Key Files to Understand

1. **code/main.py**: Entry point with path resolution for both development and packaged execution
2. **code/core/stub_processor.py**: Main orchestrator - handles file discovery, backup creation, and result management  
3. **code/core/stub_parser.py**: Parses C code for anchors, supports both traditional and new formats
4. **code/handlers/yaml_handler.py**: Manages YAML configuration with encoding detection and error recovery
5. **code/ui/app_controller.py**: Implements adapter pattern to connect UI with processing logic

### File Processing Flow
1. **Discovery**: Find all .c and .h files recursively
2. **Backup**: Create timestamped backup of entire project  
3. **Parsing**: Detect anchors/comments in source files
4. **Resolution**: Match anchors to stub code (from YAML or comments)
5. **Insertion**: Insert stub code at anchor locations with "// 通过桩插入" markers
6. **Output**: Write processed files to new timestamped directory

### YAML Configuration Format
```yaml
TC001:                    # Test Case ID
  STEP1:                 # Step ID
    segment1: |          # Segment ID (literal block scalar)
      if (data < 0) {
          printf("Invalid data\n");
          return ERROR;
      }
```

### Anchor Format in C Code
```c
// Traditional format:
// TC001 STEP1: Data validation
// code: if (data < 0) return ERROR;

// New format (YAML-based):
// TC001 STEP1 segment1
```

## Important Notes

- The application supports both GUI and command-line modes
- Encoding detection is automatic using chardet library
- All file processing includes backup creation before modification
- The build process includes syntax validation of all Python files
- PyInstaller packaging handles Tkinter dependencies and data files automatically
- The tool preserves original file encoding when writing processed files