# Worklog

## 2025-12-13
- Added a dependency-free holographic WiFi discovery map UI (`ui/holo_map/`) and a local Python map server (`bin/netreaper-map`).
- Added `wifi_scan_json` in `lib/wireless.sh` and exposed it via `netreaper wifi scan`.
- Added `netreaper wifi map` to serve the UI and read `~/.netreaper/output/wifi_scan_latest.json`.
- Updated documentation and Bats tests.

### How to run
1) `netreaper wifi scan <iface>`
2) `netreaper wifi map 8787`
3) Open `http://127.0.0.1:8787/`
