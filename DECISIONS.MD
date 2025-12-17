Decisions
2025-12-13 — Holographic WiFi map implementation approach

Chose a dependency-free canvas renderer instead of Three.js so the UI works offline and doesn't require bundling large vendor libraries.

Chose a tiny python3 HTTP server for the UI/API because NETREAPER is Bash-first and Python is commonly available on Linux security distros.

Scan export prefers nmcli (managed mode) and falls back to iw (root) to balance portability vs privilege requirements.

2025-12-16 — GUI usability choices

History loading strategy: To provide a better out‑of‑the‑box experience in the GUI, we decided to load up to 20 recent targets from the user’s history (~/.netreaper/history/scans.log and targets.log). We parse each line by whitespace and take the first token as the target, ignoring additional metadata. Although more sophisticated parsing (e.g., JSON) might capture more context, keeping it simple avoids file format assumptions and reduces failure points.

Interface detection fallback: We added a fallback mechanism in the Wireless tab’s interface refresh. If iw dev reports no interfaces, we enumerate /sys/class/net and remove the loopback interface. This may include wired adapters in the list, but it guarantees that users always see some interface options. We considered using ip link or nmcli, but opted for the filesystem because it requires no extra dependencies.

Airodump channel flag: We replaced the long --channel flag with the short -c flag in the handshake capture command after verifying that the former is not recognized by airodump-ng on common security distributions. This change ensures compatibility and successful captures.

Additional GUI features

Task cancellation design: To allow users to abort long‑running processes, we added a Stop tasks button. Internally, we modified the CommandThread class to store the subprocess.Popen instance and provide a terminate() method. The stop button iterates over active threads and terminates their processes. We considered adding per‑command kill buttons but opted for a single control to simplify the UI.

Lite mode integration: We needed an easy way for GUI users to trigger low‑resource settings already supported by the CLI. We chose a simple checkable toolbar action labelled “Lite mode”, which toggles an internal flag. When enabled, commands are prefaced with NR_LITE_MODE=1 so the Bash modules detect the environment variable. While other designs (such as a modal dialog or settings pane) were considered, a toolbar toggle offered the quickest user feedback.

Executable availability validation: We observed that running commands for absent tools (e.g., missing masscan or aircrack-ng) produced confusing errors. To improve UX, we introduced a pre‑flight check using shutil.which in execute_command. If the command's executable isn’t found, the GUI warns the user and avoids launching the command. This check skips sudo when present and only inspects the actual tool name.

BSSID history management: To assist with repeated wireless attacks, we decided to store recently used BSSIDs in memory and share them across wireless operations. A new bssid_history list and registration functions mirror the existing target history mechanism. We deliberated persisting this history to disk but postponed that change to keep the implementation lightweight for now.