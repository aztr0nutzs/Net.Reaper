# Decisions

## 2025-12-13 — Holographic WiFi map implementation approach
- Chose a dependency-free canvas renderer instead of Three.js so the UI works offline and doesn't require bundling large vendor libraries.
- Chose a tiny `python3` HTTP server for the UI/API because NETREAPER is Bash-first and Python is commonly available on Linux security distros.
- Scan export prefers `nmcli` (managed mode) and falls back to `iw` (root) to balance portability vs privilege requirements.
