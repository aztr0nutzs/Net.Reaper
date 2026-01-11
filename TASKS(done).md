Tasks

 Add holographic WiFi discovery map UI and map server

 Add netreaper wifi scan JSON export

 Add netreaper wifi map server command

 Update docs and tests

2025‑12‑16 — GUI and Usability Improvements

 Share target history across all GUI tabs and load previous scan history from ~/.netreaper/history.
Implemented by reading scans.log/targets.log during GUI initialization, storing up to 20 recent targets, and applying this list to each TargetField when it is registered. New targets are appended to the global history and propagated to all fields.

 Improve wireless interface detection in the GUI.
The Wireless tab now attempts to list Wi‑Fi interfaces via iw dev; if none are detected, it falls back to enumerating all network interfaces under /sys/class/net and excludes the loopback device. This ensures the interface selector is populated even on systems without iw or when Wi‑Fi devices are not reported.

 Correct handshake capture command.
Changed the airodump-ng invocation to use the short -c flag for channel selection instead of the unsupported --channel long option.

2025‑12‑16 — Additional GUI features

 Implement a "Stop tasks" button to allow users to terminate all running commands from the GUI.
Added a “Stop tasks” action to the toolbar. It iterates through active CommandThread instances, terminates their subprocesses and clears the task list.

 Add Lite mode toggle.
Added a checkable toolbar action labelled “Lite mode”. When enabled, GUI commands are prefixed with NR_LITE_MODE=1 so the CLI modules automatically switch to low‑resource behaviour.

 Check tool availability before execution.
Enhanced execute_command to parse the first executable in the command (ignoring sudo) and verify it exists using shutil.which(). If the tool is missing, the GUI now displays a warning instead of launching the command.

 Add shared BSSID history.
Introduced bssid_history management in the main GUI container and register_bssid_field/add_bssid_history methods. The wireless tab’s BSSID field now shares history across sessions, and BSSIDs used in deauth, WPS or handshake capture are recorded and reused