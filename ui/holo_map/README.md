# Holographic WiFi Discovery Map

This is a lightweight, dependency-free (no Three.js) 3D-ish holographic network map UI.

## Controls
- Drag: rotate
- Mouse wheel: zoom
- Click: select a node and view details
- R: reset view

## Data
The UI expects scan JSON from NETREAPER's wifi scan command via the local map server:
- `GET /api/networks/latest`
