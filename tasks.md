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


Add new functions in the modules directory (e.g., web_wizard.sh, creds_wizard.sh, wifi_takeover_wizard.sh) that handle these sequences.


Provide clear prompts between steps and automatically detect when a step has produced actionable results (e.g., if nmap finds an HTTP service, proceed to directory brute forcing).


Integrate caching so repeated wizards can reuse prior scan results.


Update bin/netreaper to register these wizards as sub‑commands or to expose them via the interactive menu.




Documentation: Update docs/TOOL_REFERENCE.md and docs/README.md with descriptions and usage examples. Provide context for when each wizard should be used.


1.2 Improve existing wizards


Auto‑fill and suggestions: Use history files (~/.netreaper/history) to pre‑populate prompts (e.g., recently used targets, wordlists) and fuzzy‑match BSSID/SSID inputs. Implement fallback to default values when the user presses Enter.


Progress display: Add progress indicators such as Step X/Y or progress bars. If using the GUI, reflect progress in a status bar or HUD.


Error handling: For each step, detect failures and either retry (with user confirmation) or offer alternate tools (e.g., masscan if nmap fails). Ensure timeouts are applied consistently and provide warnings when they trigger.


1.3 Wizard mode guidance


Provide short explanations of what each step does and the implications. For example: “We will now run enum4linux to enumerate SMB shares. This may trigger IDS alerts; ensure you have authorization.”


Add checklists before launching high‑impact steps (e.g., confirm monitor mode enabled, confirm permission for deauth attacks).


2. Implement Low‑Resource / Lite Mode
2.1 Mode flag and presets


Objective: Introduce a --lite flag (and corresponding interactive menu option) that adjusts tool behaviour for low‑end hardware or limited RAM.


Functionality:


Serialize operations rather than using multiple threads or subshells.


Use lighter tools by default (masscan instead of nmap, smaller wordlists for cracking, avoid Metasploit unless explicitly chosen).


Reduce concurrency (limit threads to a small number) and shorten timeouts.


Increase caching period and reuse results aggressively.




Integration: Add a lite_mode global variable in core.sh or a dedicated configuration file. Modify existing module functions to check this variable and adjust behaviour accordingly.


CLI/GUI exposure: Expose the --lite flag for command‑line invocations and add a toggle in the GUI and Android app.


Documentation: Explain trade‑offs of Lite mode in the README and tool reference. Include usage examples.


2.2 Resource monitoring


Implement simple CPU/RAM monitoring. If resource usage exceeds a threshold, automatically enter Lite mode or prompt the user to scale back operations.


Log resource statistics to the audit log for later analysis.


3. Automation Pipelines & Task Queuing
3.1 Pipeline framework


Create a pipeline manager in Bash (or Python if more suitable) that can queue tasks and execute them sequentially with optional concurrency control.


Design a simple job definition (e.g., JSON or YAML) specifying targets, selected modules, wizard names and parameters.


Provide CLI commands to add, list, pause, resume and cancel jobs. Integrate with the GUI so users can drag/drop tasks into a queue.


3.2 Pause/resume and checkpointing


Modify long‑running operations (e.g., hashcat, nmap) to save state periodically. Use existing caching mechanisms for Nmap and cracked hashes.


Add resume flags or continue logic in the wizards to pick up from the last successful step.


3.3 Notifications


For the GUI and mobile app, implement optional notifications (e.g., WebSocket messages, push notifications) when queued tasks complete or when critical vulnerabilities are found.


Add UI elements in the GUI/remote app to view task status.


4. Context‑Aware Recommendations


Implement a module (recommendation.sh or a Python helper) that parses scan outputs and suggests next actions. For example, after detecting an open HTTP port, recommend running nikto or gobuster.


Integrate these recommendations into the wizard flows and the CLI/GUI prompts.


Maintain a mapping of detected services or vulnerabilities to recommended tools; allow users to customise this mapping via configuration.


5. Educational Guidance and Ethics


Incorporate brief educational blurbs in wizards, the GUI and remote app explaining what each tool does and the legal/ethical considerations.


Link to external resources (e.g., OWASP guides) where appropriate.


Provide opt‑in checklists requiring users to acknowledge authorization for potentially disruptive actions (e.g., deauthentication, brute‑force attacks).


6. Extensibility


Design a plugin architecture allowing third‑party developers to contribute new modules or wizard steps without modifying core files. Define a simple API for registering commands, arguments and required capabilities.


Update docs/CONTRIBUTING.md with guidelines on writing plugins and wizards.


7. Security & Compliance


Implement role‑based permissions and optional multi‑factor authentication for the remote server (server/main.py). Allow administrators to restrict which modules are exposed to remote clients.


Enforce safe defaults in Lite mode and wizard flows. Introduce a “safe mode” that only allows passive reconnaissance until explicitly switched to an aggressive mode.


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