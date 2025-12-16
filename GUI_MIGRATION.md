# NetReaper GUI Migration Guide

## Overview
The NetReaper application has been migrated from a command-line interface (CLI) to a graphical user interface (GUI) based on the extracted design from `Gpt_reaper.html`. The GUI provides a biotech-themed interface for executing penetration testing tasks.

## Architecture
- **Backend**: FastAPI server with WebSocket support for real-time command execution.
- **Frontend**: Single-page HTML application with embedded CSS and JavaScript.
- **Communication**: WebSocket for CLI command execution, REST APIs for telemetry and actions.

## Key Changes
- CLI commands are now executed via WebSocket from the GUI.
- Visualizations and metrics are simulated but tied to real command outputs.
- Authentication via JWT tokens.
- Responsive design with accessibility features.

## API Endpoints
- `GET /`: Serves the GUI HTML.
- `POST /auth`: Authenticate and get token.
- `POST /api/telemetry`: Log telemetry data.
- `POST /api/action`: Handle actions.
- `WebSocket /ws`: Execute CLI commands.

## Usage
1. Start the server: `python3 server/main.py`
2. Open browser to `http://localhost:8443`
3. Authenticate and use the interface.

## Migration Notes
- Original CLI functionality preserved.
- All buttons wired to corresponding CLI commands where possible.
- Simulations retained for non-CLI features.

## Testing
- Unit tests for JS components.
- Integration tests for WS communication.
- E2E tests for workflows.

## Accessibility
- WCAG 2.1 AA compliant.
- Keyboard navigation, ARIA labels.

## Performance
- Efficient state management.
- Lazy loading not required for single page.