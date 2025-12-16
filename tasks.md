NetReaper Enhancement Tasks

This tasks file lays out a comprehensive plan for extending the NetReaper project. It draws from the analysis of the original NETREAPER-main and the Net.Reaper-rebuild improvements. Each task is designed for an AI engineer (or team) to follow systematically. The goals are to extend the wizard modes, implement a low‑resource mode, automate and chain attacks, and enhance user guidance and usability across CLI, GUI and remote interfaces. Where applicable, reference the relevant files or modules and ensure all modifications are thoroughly tested.

1. Expand Wizard Modes
1.1 Create task‑oriented wizards

Objective: Add new wizards that guide users through common penetration‑testing workflows. Each wizard should encapsulate a sequence of modules with clear prompts, branch logic and automated next steps.

Key workflows to implement:

Web application reconnaissance: DNS enumeration → SSL/TLS scanning → directory brute force → SQL injection testing.

Credential hunting: SMB/LDAP enumeration → password spraying → brute‑force attacks on discovered services.

Wireless takeover: Wi‑Fi survey → deauthentication to capture handshakes → offline cracking with appropriate wordlist selection.

Implementation details:

Create dedicated wizard modules. For each workflow, add a new Bash script under modules/ (e.g., modules/web_wizard.sh, modules/creds_wizard.sh, modules/wifi_takeover_wizard.sh). Each script should define a top‑level function (web_wizard(), creds_wizard(), wifi_takeover_wizard()) that orchestrates the individual steps.

Example for web_wizard.sh:

Prompt for target domain/IP; if empty, suggest the last target from ~/.netreaper/history/scans.log.

Call run_dns_enum "$target" from modules/recon.sh and capture the output path.

Parse the Nmap XML output for open HTTPS ports using a command such as grep -A1 '<port protocol="tcp" portid="443"' and, if found, call run_sslscan "$target".

If directory brute force is selected, call run_dirb "$target" or run_gobuster "$target" with a default wordlist (configurable via an environment variable). When directories are found, optionally call run_sqlmap on discovered parameters.

Implement similar stepwise functions for creds_wizard.sh (using enum4linux, crackmapexec, hydra and hashcat) and wifi_takeover_wizard.sh (using wifi_survey, run_deauth_attack, capture_handshake and run_hashcat_wifi).

Branching logic. Within each wizard function, inspect the outputs of previous commands to decide whether to continue or skip a step. For example, if no SMB ports (139/445) are discovered in the credential wizard, skip enumeration and jump to the next module.

Result caching. Use the existing caching directories (e.g., ~/.netreaper/cache/scans) to store intermediate results. Before running a step, check for a cached file (by hashing the target and parameters) and offer the user the option to reuse it.

Menu integration. In bin/netreaper, add sub‑commands such as web-wizard, creds-wizard and wifi-wizard. Update the interactive main menu to include these wizards under a new “🧙 Wizards” section. Provide short descriptions and hotkeys.

Documentation: Update docs/TOOL_REFERENCE.md and docs/README.md with descriptions and usage examples. Provide context for when each wizard should be used.

1.2 Improve existing wizards

Auto‑fill and suggestions: Enhance the existing history mechanisms in modules/*.sh to read recent entries from ~/.netreaper/history. Implement helper functions like get_recent_targets() and get_recent_wordlists() in a shared library (e.g., lib/history.sh) and call them in wizards to pre‑populate prompts. Use grep or jq to fuzzy‑match BSSID/SSID from wifi_scan_latest.json when asking for wireless targets. Provide a default value when the user presses Enter.

Progress display: Add variables current_step and total_steps at the beginning of each wizard and increment current_step after each stage. Display progress using a formatted string such as printf "[%d/%d] %s\n" "$current_step" "$total_steps" "Description". In the PyQt6 GUI, update a QProgressBar or status label via signal/slot connections. In the Android app, update the UI state within a coroutine to reflect progress.

Error handling: Wrap each external command invocation in a timeout and conditional check. If a command exits non‑zero, present the user with a menu: retry with different parameters, fall back to an alternative tool (e.g., masscan when nmap fails), or skip the step. Avoid using set -e globally; instead handle failures locally so that the wizard can continue gracefully.

1.3 Wizard mode guidance

Help text implementation: For each wizard, include a --help option that prints a detailed outline of the steps and warns about potential impact. Use a cat << 'EOF' block at the top of each wizard script so that netreaper web-wizard --help displays a human‑readable description like: “This wizard performs DNS enumeration, SSL scanning, directory brute forcing and optional SQL injection testing. Ensure you have authorization before running intrusive scans.”

Pre‑flight checklists: Define a preflight_checks() function in each wizard that prompts the user to confirm prerequisites (e.g., monitor mode enabled, VPN disconnected, target scope approved). Abort or switch to passive reconnaissance if the user declines. For attacks like deauthentication, explicitly ask the user to confirm they are authorized.

2. Implement Low‑Resource / Lite Mode
2.1 Mode flag and presets

Objective: Introduce a --lite flag (and corresponding interactive menu option) that adjusts tool behaviour for low‑end hardware or limited RAM.

Functionality:

Serialize operations rather than using multiple threads or subshells.

Use lighter tools by default (masscan instead of nmap, smaller wordlists for cracking, avoid Metasploit unless explicitly chosen).

Reduce concurrency (limit threads to a small number) and shorten timeouts.

Increase caching period and reuse results aggressively.

Integration: Introduce an environment variable NR_LITE_MODE and define a helper is_lite() in lib/core.sh. Set NR_LITE_MODE=${NR_LITE_MODE:-0} at startup. Modify existing module functions to call is_lite() and branch to alternative logic: for example, reduce thread counts, skip heavy enumeration scripts, or switch to nmap -T2 with fewer scripts when lite mode is enabled.

CLI/GUI exposure: To expose the --lite flag:

CLI: In bin/netreaper, update the argument parser to include a --lite or -L option. Set NR_LITE_MODE=1 when this flag is present before sourcing any modules. Example:

# Parse global options
while [[ $# -gt 0 ]]; do
  case "$1" in
    -L|--lite) export NR_LITE_MODE=1; shift ;;
    # ... existing options ...
    *) break ;;
  esac
done


Also display the new option in the help output (netreaper --help) with a description of its purpose.

Interactive menu: In the TUI menu defined in bin/netreaper or lib/menu.sh, add a toggle item labelled “Enable Lite Mode” under settings. When selected, toggle the environment variable and update the status indicator in the menu header. Persist the choice to ~/.netreaper/config so it is remembered across sessions.

PyQt6 GUI: In qt/client.py, add a checkbox or switch labelled “Lite mode” in the global settings pane. When toggled, emit a signal that calls the CLI backend with --lite appended to all commands. Update the UI to visually indicate when Lite mode is active (e.g., change the title bar color or show a badge). Ensure that changes propagate to the remote server by including a JSON field "lite": true in API requests via WebSockets.

Android app: In the Kotlin project, modify the preferences screen to include a “Lite Mode” switch that stores its state in SharedPreferences. When executing remote commands through the WebSocket connection, include a lite field in the request message. Update the UI to reflect the current mode on the main dashboard.

Testing: Verify that enabling/disabling Lite mode via CLI, GUI, and remote interfaces sets NR_LITE_MODE correctly and affects module behaviour as expected.

Documentation: Explain trade‑offs of Lite mode in the README and tool reference. Include usage examples.

2.2 Resource monitoring

Implement simple CPU/RAM monitoring. If resource usage exceeds a threshold, automatically enter Lite mode or prompt the user to scale back operations.

Log resource statistics to the audit log for later analysis.

Implementation details: To implement robust resource monitoring:

Monitoring implementation: Create a Bash function monitor_resources() in lib/monitor.sh that reads current CPU and memory usage periodically using /proc and grep. For example, compute CPU load with awk '{u=$2+$4; t=$2+$4+$5} END {print (u/t)*100}' /proc/stat and memory usage with free -m. Accept threshold values via environment variables (NR_MAX_CPU, NR_MAX_MEM) defaulting to 80% CPU and 75% memory.

Run monitor_resources in the background at the start of each wizard or long‑running module. If usage exceeds thresholds for more than a configurable number of checks (e.g., 3 consecutive samples), automatically set NR_LITE_MODE=1 and log a warning to the console and audit log. Provide a prompt to the user allowing them to continue in Lite mode or abort.

Integrate this monitoring into Python components by adding an asynchronous task in server/main.py using psutil to sample system metrics every few seconds. When thresholds are breached, send a notification to connected clients via WebSockets indicating that resource limits were reached and suggesting to switch to Lite mode.

Audit logging: Append resource usage snapshots to ~/.netreaper/audit.log with timestamps and the current command context. Example log entry: 2025-12-16T14:30:02Z CPU=92 MEM=78 NR_LITE_MODE=0 current_task=web_wizard.

Configuration: Document configurable thresholds in docs/CONFIG.md and allow users to override them via ~/.netreaper/config.

3. Automation Pipelines & Task Queuing
3.1 Pipeline framework

Create a pipeline manager in Bash (or Python if more suitable) that can queue tasks and execute them sequentially with optional concurrency control.

Design a simple job definition (e.g., JSON or YAML) specifying targets, selected modules, wizard names and parameters.

Provide CLI commands to add, list, pause, resume and cancel jobs. Integrate with the GUI so users can drag/drop tasks into a queue.

Implementation details: Provide a concrete design for the pipeline manager:

Manager implementation: Implement a new script bin/nrpipeline written in Python (for better concurrency and data handling) using the asyncio library. The script should:

Read a job queue from a JSON file in ~/.netreaper/jobs.json where each job is an object containing id, target, wizard, params, status and created_at.

Expose subcommands: add, list, pause, resume, cancel via argparse. The add subcommand accepts a JSON or YAML job definition (see next bullet) and appends it to the queue file. The list command prints a table of jobs with statuses (queued/running/completed/paused/failed).

Launch jobs sequentially or concurrently depending on a configuration parameter max_concurrency. Use asyncio.create_subprocess_exec to call underlying wizards or module scripts. Capture their stdout/stderr and update the job status in the JSON file.

Persist intermediate state so that if the script is interrupted, it can resume remaining jobs on restart.

Job specification: Define a job file format in YAML or JSON with fields such as:

id: <auto‑generated UUID>
target: 192.168.1.10
wizard: web_wizard
params:
  wordlist: /usr/share/wordlists/common.txt
  skip_ssl: false


Provide example templates in docs/examples/ and mention them in the documentation.

CLI integration: Add netreaper queue commands that internally call nrpipeline via subprocess. For instance, netreaper queue add --job job.yaml should wrap around nrpipeline add --file job.yaml. Similarly, add new menu items to the TUI for managing queued jobs (list, pause, resume, cancel).

GUI integration: In the PyQt6 GUI, implement a task queue panel that displays the current job list using a QTableWidget. Users should be able to drag and drop tasks from a list of available wizards onto the queue panel. Use WebSockets to send queue commands to the backend, where nrpipeline runs. Display real‑time updates using signals/slots and asynchronous event handlers.

Android integration: Add a queue management fragment in the Kotlin app that shows queued tasks. Use the existing WebSocket client to communicate queue commands to the server API.

3.2 Pause/resume and checkpointing

Modify long‑running operations (e.g., hashcat, nmap) to save state periodically. Use existing caching mechanisms for Nmap and cracked hashes.

Add resume flags or continue logic in the wizards to pick up from the last successful step.

Implementation details: Ensure long‑running operations can be paused and resumed gracefully:

Saving state: For nmap, specify the --resume option by saving the scan’s initial command string to a file (.nmapstate) and passing it when a resume is requested. For hashcat, call hashcat --session <name> --restore to continue from the last checkpoint. In each wizard script, maintain a status file (e.g., in ~/.netreaper/checkpoints) that records the current step and any relevant state (such as captured handshake files). Write a helper save_checkpoint <wizard> <step> that writes this status along with a timestamp.

After each major stage in a wizard, call save_checkpoint so that progress is persisted. Provide a command-line option --resume for each wizard that, when invoked, reads the checkpoint file and jumps directly to the recorded step using a case statement.

User control: Implement pause and resume commands in the pipeline manager. When a user pauses a job, send a SIGSTOP to the underlying process via Python’s os.kill or asyncio API and record its PID. When resuming, send SIGCONT. For jobs that cannot be cleanly paused (e.g., some network scans), provide a safe way to abort and restart from the last checkpoint.

State sync: Ensure that checkpoint files and job statuses are synchronized across the CLI, GUI, and Android app. When a user resumes or cancels a job from any interface, update the queue file and send notifications accordingly.

3.3 Notifications

For the GUI and mobile app, implement optional notifications (e.g., WebSocket messages, push notifications) when queued tasks complete or when critical vulnerabilities are found.

Add UI elements in the GUI/remote app to view task status.

Implementation details: Implement comprehensive notification support across the stack:

Backend notifications: In the remote server (server/main.py), implement a WebSocket channel named /notifications that broadcasts JSON messages whenever a job status changes (e.g., {"job_id": "...", "status": "completed", "message": "Web wizard finished successfully"}). Use FastAPI’s WebSocket endpoints to manage connections and broadcast to all subscribed clients.

Add a simple publish/subscribe mechanism within nrpipeline that posts to this channel whenever it updates a job status. Use uvicorn or a similar ASGI server to run the WebSocket server in the same process as existing FastAPI endpoints.

GUI implementation: In the PyQt6 client, create a WebSocket client using websockets or QWebSocket to listen to the /notifications endpoint. When a message is received, display a pop‑up toast notification using QSystemTrayIcon or a custom dialog. Provide a preferences option to enable/disable notifications.

Mobile notifications: In the Android app, use the existing WebSocket client to subscribe to /notifications. On receiving messages, display push notifications using Android’s NotificationCompat API. Allow the user to customize notification behaviour (sound, vibration) in settings.

Task status UI: Extend the GUI and Android task queue panel to include status columns or icons (queued, running, paused, completed, failed). Update these in real time based on notifications from the backend.

4. Context‑Aware Recommendations

Implement a module (recommendation.sh or a Python helper) that parses scan outputs and suggests next actions. For example, after detecting an open HTTP port, recommend running nikto or gobuster.

Integrate these recommendations into the wizard flows and the CLI/GUI prompts.

Maintain a mapping of detected services or vulnerabilities to recommended tools; allow users to customise this mapping via configuration.

Implementation details: Provide a concrete recommendation engine:

Recommendation engine: Develop a Python script lib/recommendation.py that reads output from scans (e.g., Nmap XML, tool logs) and extracts service names, versions and known vulnerabilities using XPath or xml.etree.ElementTree. Create a static mapping file (conf/recommendations.yaml) where keys are service regex patterns and values are lists of recommended follow‑up modules or wizards. Example:

http:
  - nikto
  - gobuster
  - sqlmap
smb:
  - enum4linux
  - smb_map


Provide functions get_recommendations(service_list) and suggest_next_actions(scan_output_file) that return human‑readable suggestions. Expose these functions as part of the CLI via netreaper recommend --scan scan.xml.

Wizard integration: At the end of each wizard or step, call the recommendation engine to analyze results and print suggestions. If running interactively, prompt the user to launch a recommended module or add it to the pipeline queue. For example: “We detected an open HTTP port. Would you like to run gobuster? [Y/n]”.

GUI integration: In the GUI and mobile app, display recommendations in a sidebar or modal window after a scan completes. Provide buttons to automatically enqueue recommended actions.

Customisation: Allow users to override or extend the recommendation mapping by creating a file at ~/.netreaper/recommendations.yaml. Merge this with the default mapping at runtime.

5. Educational Guidance and Ethics

Incorporate brief educational blurbs in wizards, the GUI and remote app explaining what each tool does and the legal/ethical considerations.

Link to external resources (e.g., OWASP guides) where appropriate.

Provide opt‑in checklists requiring users to acknowledge authorization for potentially disruptive actions (e.g., deauthentication, brute‑force attacks).

6. Extensibility

Design a plugin architecture allowing third‑party developers to contribute new modules or wizard steps without modifying core files. Define a simple API for registering commands, arguments and required capabilities.

Update docs/CONTRIBUTING.md with guidelines on writing plugins and wizards.

Implementation details: Define a clear plugin architecture:

Plugin system design: Create a plugins/ directory at the project root where each plugin resides in its own subdirectory. Each plugin must include:

A plugin.json manifest file containing metadata (name, version, author, description, commands) and a list of capabilities (e.g., needs root, network access).

One or more script files (Bash or Python) implementing the plugin’s functionality. Functions should be namespaced with the plugin name to avoid collisions (e.g., myplugin_do_something).

Plugin loader: Develop a Bash function load_plugins() in lib/plugins.sh that iterates over plugins/*/plugin.json, sources each script listed in the manifest, and registers the plugin’s commands into a global associative array PLUGIN_COMMANDS. Provide a helper run_plugin_command <command> <args> that looks up the appropriate function and executes it.

Command registration: In the manifest, specify commands along with usage strings and a pointer to the function implementing them. Example plugin.json:

{
  "name": "http-vuln-checker",
  "version": "1.0.0",
  "commands": {
    "check-http": {
      "function": "http_vuln_checker_check_http",
      "description": "Scan HTTP services for common vulnerabilities"
    }
  }
}


Core integration: Modify bin/netreaper to call load_plugins at startup and merge plugin commands into the existing command dispatch logic. Display plugin commands in the CLI help and interactive menu grouped under “Plugins”. Ensure that plugin failures do not crash the core by wrapping plugin calls in trap handlers.

Documentation: Expand docs/CONTRIBUTING.md with a “Writing Plugins” section explaining the manifest format, directory structure, namespacing requirements, and example code. Encourage developers to contribute via pull requests and provide guidelines for security review.

7. Security & Compliance

Implement role‑based permissions and optional multi‑factor authentication for the remote server (server/main.py). Allow administrators to restrict which modules are exposed to remote clients.

Enforce safe defaults in Lite mode and wizard flows. Introduce a “safe mode” that only allows passive reconnaissance until explicitly switched to an aggressive mode.

Implementation details: Strengthen security of the remote server and user flows:

Role‑based access control (RBAC): Modify server/main.py to define user roles (e.g., admin, analyst, guest) and associated permissions. Store user credentials and role assignments in a secure database (sqlite or postgres) or configuration file with salted password hashes. Extend the FastAPI routes to check the requesting user’s role before executing any command. For example, only admins can run destructive modules (e.g., deauth, exploit), while analysts can run reconnaissance and enumeration. Implement endpoints for administrators to manage users and roles. Use JWT tokens containing role claims and validate them on each request.

Multi‑factor authentication: Integrate TOTP-based MFA using a library like pyotp. When a user logs in, require a one‑time code from a time-based authenticator app. Store users’ TOTP secrets securely. Update server/auth.py to issue JWTs only after successful MFA verification.

Safe mode: Implement a global NR_SAFE_MODE flag, defaulting to enabled. When safe mode is active, restrict wizard flows to passive reconnaissance modules (e.g., port scanning, OS detection) and disable active attacks (e.g., brute force, deauthentication) until the user explicitly toggles safe mode off via a CLI flag (--unsafe), GUI setting or admin configuration. Check this flag in each wizard’s preflight check and branch accordingly.

User awareness: Display a warning message when switching out of safe mode, both in CLI and GUI, requiring explicit confirmation. Persist the safe mode state in ~/.netreaper/config.

Audit trail: Enhance ~/.netreaper/audit.log to record which user executed which modules along with timestamps and whether safe mode was active. Include role identifiers in audit entries for accountability.

8. Testing and Quality Assurance

Unit tests: Write tests for all new functions, focusing on branching logic and error handling. Use Bats for Bash modules and pytest for Python components.

Integration tests: Simulate end‑to‑end wizard runs under both normal and Lite modes. Verify caching, fallbacks, and resume functionality.

Performance tests: Measure resource usage on low‑end hardware. Adjust thresholds and defaults based on empirical results.

Security reviews: Audit new code for security issues, especially in the remote server and any new Python modules.

9. Documentation Updates

TASKS.md: Claim each task when work begins, mark it complete when finished, and link to relevant commits or pull requests.

WORKLOG.md: Document work performed, including assumptions, difficulties and how to run new features. Include dates and your initials.

DECISIONS.md: Record significant architectural decisions (e.g., choice of frameworks, resource thresholds, security measures) with justification.

README & Tool Reference: Update to reflect new wizards, Lite mode, pipelines and usage examples. Ensure cross‑platform instructions for Linux, GUI and Android remain accurate.

10. Double‑Check & Verification

After implementing each task:

Code review: Have a second AI or team member review the code changes for correctness, style and security.

Run tests: Ensure the full test suite passes. Add tests as needed if coverage is missing.

Manual testing: Execute each wizard and Lite mode on a test environment. Confirm that prompts, defaults and fallbacks work as expected.

Update documentation: Verify that all docs reflect the current behaviour. Cross‑link new features where appropriate.

Tag and version: Increment the version number in VERSION and update any version badges or changelogs.

By following this task list, the AI engineer(s) will systematically implement and verify all proposed improvements, ensuring that NetReaper becomes more powerful, user friendly and reliable across a broad range of hardware and use cases.