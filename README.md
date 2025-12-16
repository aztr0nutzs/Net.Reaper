<p align="center">
  <pre>
╔══════════════════════════════════════════════════════════════════════════════════════╗
║ ███╗   ██╗███████╗████████╗██████╗ ███████╗ █████╗ ██████╗ ███████╗██████╗           ║
║ ████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗          ║
║ ██╔██╗ ██║█████╗     ██║   ██████╔╝█████╗  ███████║██████╔╝█████╗  ██████╔╝          ║
║ ██║╚██╗██║██╔══╝     ██║   ██╔══██╗██╔══╝  ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗          ║
║ ██║ ╚████║███████╗   ██║   ██║  ██║███████╗██║  ██║██║     ███████╗██║  ██║          ║
║ ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝          ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
  </pre>
</p>

<h1 align="center">NETREAPER</h1>
<p align="center"><strong>Offensive Security Framework</strong></p>
<p align="center">v6.3.4 — Phase 3: Core Infrastructure</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-6.3.4-red?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-Linux-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/shell-Bash%205.0+-green?style=flat-square" alt="Shell">
</p>

---

> **"Some tools scan. Some tools attack. I do both."**

NETREAPER is a modular Bash-based offensive security toolkit that unifies 70+ security tools behind a single CLI. Built for penetration testers, red teamers, and security researchers who need a fast, scriptable interface with proper safety guardrails.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Nerds489/NETREAPER.git
cd NETREAPER

# Install (requires root for system-wide installation)
sudo ./install.sh
```

The `install.sh` wrapper delegates to `bin/netreaper-install`, which handles tool installation, system-wide symlinks, and dependency management.

> **NETREAPER v5.x monolithic installs are obsolete and unsupported.**
> The installer **hard-removes** legacy binaries and will **fail** if removal is not possible.
> If you have `/usr/local/bin/netreaper` from v5.x, it will be deleted during installation.

**Clean reinstall (removes all artifacts first):**

```bash
sudo ./reinstall-netreaper.sh
```

For CI/automation (non-interactive):

```bash
sudo NR_NON_INTERACTIVE=1 NR_FORCE_REINSTALL=1 ./reinstall-netreaper.sh
```

**Running locally (without install):**

```bash
# Root wrappers in project root delegate to bin/
./netreaper --help
./netreaper-install --help
```

---

## Installer Guarantees

The `install.sh` installer provides the following guarantees to ensure `netreaper` is always callable after installation:

### Wrapper Scripts

The installer creates **thin wrapper scripts** in a system PATH directory (e.g., `/usr/local/bin/netreaper`) that point to the actual executables in `bin/netreaper` and `bin/netreaper-install`. This ensures:

- `netreaper` works from any directory
- No need to modify PATH manually in most cases
- Clean separation between system binaries and project source

### Install Directory Selection

The installer uses `_select_install_dir()` to choose the best installation directory:

1. **`/usr/local/bin`** — preferred if it exists and is in PATH
2. **`/usr/bin`** — fallback if `/usr/local/bin` is unavailable
3. **Custom fallback** — if neither is in PATH, the installer creates a PATH drop-in file

### PATH Drop-in File

If the selected install directory is not in the user's PATH, the installer creates `/etc/profile.d/netreaper.sh`:

```bash
# /etc/profile.d/netreaper.sh
export PATH="/usr/local/bin:$PATH"
```

This ensures the install directory is added to PATH for all users on next login.

### Hard-Fail Verification

After installation completes, the installer runs:

```bash
command -v netreaper
```

If this command fails (i.e., `netreaper` is not callable), **the installer exits with an error**. This prevents silent installation failures where the binary exists but isn't accessible.

### Argument Guard

`bin/netreaper-install` only executes its main logic if arguments are provided. Running it without arguments displays help and exits, preventing accidental execution.

---

## Tool Detection & Auto-Install

NETREAPER provides intelligent tool detection and automatic installation that works across all major Linux distributions.

### Tool Search Paths

The `check_tool()` and `get_tool_path()` functions search for tools in the following directories (defined in `TOOL_SEARCH_PATHS`):

```
/usr/bin
/usr/local/bin
/usr/sbin
/usr/local/sbin
/sbin
/bin
/opt/bin
~/.local/bin
~/go/bin
```

This ensures tools installed via system packages, pip, cargo, go, or manual installation are all detected.

### Distro-Aware Package Name Resolution

Different Linux distributions use different package names for the same tool. The `tool_package_name()` function resolves the correct package name based on your distro family:

| Tool | Debian/Ubuntu | RHEL/Fedora | Arch |
|------|---------------|-------------|------|
| `dig` | `dnsutils` | `bind-utils` | `bind` |
| `tshark` | `tshark` | `wireshark-cli` | `wireshark-cli` |
| `netcat` | `netcat-openbsd` | `nmap-ncat` | `openbsd-netcat` |
| `aircrack-ng` | `aircrack-ng` | `aircrack-ng` | `aircrack-ng` |
| `airodump-ng` | `aircrack-ng` | `aircrack-ng` | `aircrack-ng` |
| `aireplay-ng` | `aircrack-ng` | `aircrack-ng` | `aircrack-ng` |
| `airmon-ng` | `aircrack-ng` | `aircrack-ng` | `aircrack-ng` |

### Auto-Install Behavior

When `auto_install_tool()` is called:

1. Detects the current distro family (debian, redhat, arch, suse, alpine)
2. Calls `tool_package_name()` to resolve the correct package name
3. Installs using the appropriate package manager (`apt`, `dnf`, `pacman`, etc.)

**Example:**

```bash
# On Ubuntu, installs 'dnsutils' package
auto_install_tool dig

# On Fedora, installs 'bind-utils' package
auto_install_tool dig

# On Arch, installs 'bind' package
auto_install_tool dig
```

### Empty Tool Name Protection

Both `check_tool()` and `get_tool_path()` reject empty tool names and return 1, preventing accidental misuse.

---

## Core Features

- **70+ Tools Behind One CLI** — Nmap, Aircrack-ng, Metasploit, Hydra, and more, all accessible via unified commands
- **Dry-Run Mode** — Preview commands without execution (`--dry-run`)
- **Modular Architecture** — Separate `bin`, `lib`, and `modules` directories for clean organization
- **Structured Logging & Audit Trail** — Daily log rotation with separate audit logs for compliance
- **Safety & Authorization Model** — Target validation, protected IP ranges, and authorization prompts
- **Non-Interactive / CI-Safe** — Explicit opt-in flags for automated pipelines

---

## Architecture Overview

```
NETREAPER/
├── netreaper              # Root wrapper → bin/netreaper
├── netreaper-install      # Root wrapper → bin/netreaper-install
├── install.sh             # Installer wrapper → bin/netreaper-install
├── VERSION                # Single source of truth for version
├── bin/
│   ├── netreaper          # Main CLI dispatcher
│   └── netreaper-install  # Tool installer
├── lib/
│   ├── version.sh         # NETREAPER_ROOT + VERSION resolution
│   ├── core.sh            # Logging, paths, directories, error handling, sudo helpers
│   ├── ui.sh              # Banners, menus, prompts, confirmations
│   ├── safety.sh          # Target validation, authorization, unsafe mode
│   ├── detection.sh       # Distro, package manager, tool, interface detection
│   ├── config.sh          # Persistent configuration management
│   └── utils.sh           # Timestamps, backups, safe file operations, tool execution
├── modules/
│   ├── recon.sh           # Reconnaissance tools
│   ├── scanning.sh        # Port scanning, service enumeration
│   ├── wireless.sh        # WiFi attacks, monitor mode, handshake capture
│   ├── exploit.sh         # Exploitation frameworks
│   ├── credentials.sh     # Password attacks, hash cracking
│   ├── traffic.sh         # Traffic analysis, MITM
│   ├── osint.sh           # Open source intelligence
│   └── stress.sh          # Stress testing, DoS simulation
├── docs/                  # Documentation (HOWTO, QUICKREF, etc.)
└── tests/                 # Test suites (bats, smoke tests)
```

---

## Library Descriptions

| File | Purpose |
|------|---------|
| `version.sh` | Resolves `NETREAPER_ROOT` and reads `VERSION` file; prevents version drift |
| `core.sh` | Logging system, color definitions, directory setup, exit codes, privilege handling, dry-run, `die`/`try`/`require_tool` |
| `ui.sh` | Banner display, input sanitization, prompts (`confirm`, `confirm_dangerous`, `select_option`), progress indicators |
| `safety.sh` | IP validation, CIDR matching, protected ranges, `validate_target()`, authorization checks, unsafe mode |
| `detection.sh` | Distro detection, package manager setup, tool checks with `TOOL_SEARCH_PATHS`, `tool_package_name()` for distro-aware resolution, wireless interface detection |
| `config.sh` | Persistent configuration: `init_config()`, `config_get/set/show/edit`, atomic file writes |
| `utils.sh` | Timestamps, file backups, cleanup handlers, safe file operations (`safe_rm`, `safe_copy`, `safe_move`), tool execution wrappers |

---

## Logging System

NETREAPER provides structured logging with six severity levels:

| Level | Function | Symbol | Use Case |
|-------|----------|--------|----------|
| DEBUG | `log_debug()` | `~` | Detailed diagnostic information |
| INFO | `log_info()` | `*` | General operational messages |
| SUCCESS | `log_success()` | `✓` | Successful operations |
| WARNING | `log_warning()` | `!` | Potential issues, cautions |
| ERROR | `log_error()` | `✗` | Errors that don't halt execution |
| FATAL | `log_fatal()` | `☠` | Critical errors that exit |

### Log File Locations

```
~/.netreaper/logs/netreaper_YYYYMMDD.log   # Operation logs (daily rotation)
~/.netreaper/logs/audit_YYYYMMDD.log       # Audit trail (actions, targets, results)
```

### Logging Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NETREAPER_LOG_LEVEL` | `1` | Minimum level to log (0=DEBUG, 1=INFO, 2=SUCCESS, 3=WARNING, 4=ERROR, 5=FATAL) |
| `NETREAPER_FILE_LOGGING` | `1` | Enable file logging (0 to disable) |

### Audit Logging

All significant actions are recorded via `log_audit()`:

```
[2025-01-15 14:30:22] USER=root ACTION=SCAN TARGET="192.168.1.1" RESULT="success" PID=12345
```

---

## Privilege & Sudo Handling

NETREAPER provides several functions for managing root privileges:

| Function | Description |
|----------|-------------|
| `is_root()` | Returns 0 if running as root (EUID=0) |
| `require_root()` | Logs error and returns 1 if not root; provides hint to re-run with sudo |
| `run_with_sudo()` | Executes command with sudo if not already root |
| `elevate_if_needed()` | Prompts user to elevate privileges; re-execs script as root if approved |
| `can_get_root()` | Checks if root access is possible (already root, passwordless sudo, or TTY) |

**Operations requiring root** (defined in `ROOT_OPS` array):

```
wifi, scan, stress, exploit, traffic, sniff, mitm, capture, inject
```

**Non-interactive behavior:**

- `elevate_if_needed()` returns error if `NR_NON_INTERACTIVE=1` or no TTY
- Use `sudo` explicitly in CI pipelines

---

## Safety & Target Validation

### validate_target()

The `validate_target()` function is the primary safety gate for all operations:

- **Accepts:** IP address, CIDR notation, or hostname
- **Resolves hostnames** to IP addresses (via `dig`, `host`, or `getent`)
- **Checks protected ranges** — blocks loopback, link-local, multicast, broadcast, reserved
- **Detects private vs public IPs** — warns and requires confirmation for public targets

### Protected Ranges

The `DEFAULT_PROTECTED_RANGES` array blocks these CIDR ranges:

| Range | Description |
|-------|-------------|
| `127.0.0.0/8` | Loopback |
| `169.254.0.0/16` | Link-local |
| `224.0.0.0/4` | Multicast |
| `240.0.0.0/4` | Reserved |
| `255.255.255.255/32` | Broadcast |
| `0.0.0.0/8` | Current network |

### Validation Functions

| Function | Description |
|----------|-------------|
| `is_valid_ip()` | Validates IPv4 address format (each octet 0–255) |
| `is_valid_cidr()` | Validates CIDR notation (IP + prefix 0–32) |
| `is_private_ip()` | Checks if IP is RFC1918 private |
| `is_protected_ip()` | Checks if IP falls within any `DEFAULT_PROTECTED_RANGES` |
| `is_dangerous_range()` | Blocks broad ranges like `0.0.0.0/0` |

### Public IP Behavior

- **Normal mode:** Warns user and requires `confirm_dangerous()` confirmation
- **Unsafe mode:** Allows with logging; no confirmation required

---

## Dangerous Operations & Confirmations

### Confirmation Functions

| Function | Description |
|----------|-------------|
| `confirm()` | Simple yes/no confirmation with default; returns 0 or 1 |
| `confirm_dangerous()` | Requires typing exact phrase (e.g., `YES`) to proceed; shows warning banner |
| `prompt_input()` | Collects input with optional validator and secret mode |
| `select_option()` | Displays numbered menu; returns selected option |

### Interactive Mode Examples

```bash
# confirm() example
confirm "Continue with scan?" "n"  # Default: no

# confirm_dangerous() example — requires typing exact phrase
confirm_dangerous "Delete all logs?" "DELETE"
```

### Non-Interactive Mode Behavior

| Function | Default Behavior | Override |
|----------|------------------|----------|
| `confirm()` | Uses default value | N/A |
| `confirm_dangerous()` | Blocked (returns 1) | `NR_UNSAFE_MODE=1` or `NR_FORCE_DANGEROUS=1` |
| `select_option()` | Fails (returns 1) | Set `NR_NON_INTERACTIVE_DEFAULT_INDEX=N` |
| `prompt_input()` | Returns default value | N/A |

---

## Non-Interactive & CI Mode

NETREAPER detects non-interactive mode when:

- `NR_NON_INTERACTIVE=1` is set, or
- No TTY is attached (`[[ ! -t 0 ]]`)

### Behavior Matrix

| Function | Interactive | Non-Interactive (default) | Non-Interactive + Unsafe Mode |
|----------|-------------|---------------------------|-------------------------------|
| `check_authorization()` | Prompts for "I AM AUTHORIZED" | Blocked | Allowed with `NR_AUTO_AUTHORIZE_NON_INTERACTIVE=1` |
| `confirm_dangerous()` | Prompts for exact phrase | Blocked | Auto-accepts |
| `select_option()` | Shows menu, waits for input | Fails | Uses `NR_NON_INTERACTIVE_DEFAULT_INDEX` |
| `confirm()` | Prompts y/n | Uses default | Uses default |
| `elevate_if_needed()` | Prompts for elevation | Fails | Fails (use explicit sudo) |

### Enabling Dangerous Operations in CI

```bash
# Full unsafe mode — bypasses all safety checks
export NR_UNSAFE_MODE=1
export NR_NON_INTERACTIVE=1
export NR_AUTO_AUTHORIZE_NON_INTERACTIVE=1
netreaper scan 192.168.1.1

# Allow only dangerous confirmations (without full unsafe mode)
export NR_NON_INTERACTIVE=1
export NR_FORCE_DANGEROUS=1
netreaper scan 192.168.1.1

# Menu selection in non-interactive mode
export NR_NON_INTERACTIVE=1
export NR_NON_INTERACTIVE_DEFAULT_INDEX=0  # Select first option (0-based)
netreaper wizard scan
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NETREAPER_LOG_LEVEL` | `1` | Log level: 0=DEBUG…5=FATAL |
| `NETREAPER_FILE_LOGGING` | `1` | Enable file logging (0 to disable) |
| `NR_NON_INTERACTIVE` | `0` | Force non-interactive mode (1 to enable) |
| `NR_UNSAFE_MODE` | `0` | Bypass safety checks; accepts `1`, `true`, `yes`, `y` |
| `NR_FORCE_DANGEROUS` | `0` | Allow `confirm_dangerous()` in non-interactive mode |
| `NR_AUTO_AUTHORIZE_NON_INTERACTIVE` | `0` | Auto-authorize in non-interactive mode (requires unsafe) |
| `NR_NON_INTERACTIVE_DEFAULT_INDEX` | (unset) | 0-based index for `select_option()` in non-interactive mode |
| `NR_DRY_RUN` | `0` | Print commands instead of executing (1 to enable) |
| `NO_COLOR` | `0` | Disable colored output (1 to enable) |
| `DEBUG` | `false` | Enable debug output (`true` to enable) |
| `VERBOSE` | `false` | Enable verbose output (`true` to enable) |
| `QUIET` | `false` | Suppress non-error console output (`true` to enable) |

---

## Configuration

NETREAPER supports persistent configuration via a config file. Settings are applied at startup and can be overridden by environment variables.

### Config File Location

```
~/.netreaper/config/config.conf
```

### Configuration Commands

```bash
# Show all configuration
netreaper config show

# Get a specific value (outputs raw value only, suitable for scripting)
netreaper config get log_level

# Set a value (persists to file)
netreaper config set log_level DEBUG

# Edit config file interactively
netreaper config edit

# Show config file path
netreaper config path

# Reset to defaults
netreaper config reset
```

### Config Get Output

The `config get` command outputs **only the raw value** with no headers, colors, or logging to stdout:

```bash
$ netreaper config get log_level
INFO

$ netreaper config get file_logging
true
```

This makes it safe for use in scripts and CI pipelines:

```bash
level=$(netreaper config get log_level)
[[ "$level" == "INFO" ]] && echo "Default level"
```

### Default Configuration Values

| Key | Default | Description |
|-----|---------|-------------|
| `log_level` | `INFO` | Logging threshold: DEBUG, INFO, SUCCESS, WARNING, ERROR, FATAL |
| `file_logging` | `true` | Enable logging to file (`true`/`false`) |
| `default_scan_type` | `standard` | Default scan type: quick, standard, full, stealth |
| `confirm_dangerous` | `true` | Require confirmation for dangerous operations |
| `warn_public_ip` | `true` | Warn when targeting public IP addresses |
| `default_wordlist` | `/usr/share/wordlists/rockyou.txt` | Default wordlist for password attacks |
| `non_interactive_default_index` | `0` | Default menu selection index (0-based) |
| `unsafe_mode` | `false` | Disable safety checks (NOT RECOMMENDED) |

### Environment Variable Precedence

Environment variables **override** config file settings for CI/pipeline control:

```bash
# Config file sets log_level=INFO, but env var overrides
NETREAPER_LOG_LEVEL=0 netreaper status  # Uses DEBUG level

# Environment overrides for CI (these always take precedence)
NR_NON_INTERACTIVE=1      # Forces non-interactive mode
NR_UNSAFE_MODE=1          # Bypasses safety checks
```

**Priority order (highest to lowest):**

1. Environment variables (`NR_*`, `NETREAPER_*`)
2. Config file (`~/.netreaper/config/config.conf`)
3. Built-in defaults

**Note:** The config file is for user defaults and preferences. Safety-critical gates should be controlled via explicit environment variables in CI pipelines, not config file overrides.

---

## CLI Usage Examples

```bash
# Show help
netreaper --help
netreaper help

# Show version (reads from VERSION file)
netreaper --version

# Check tool status (displays tool availability dashboard)
netreaper status

# Dry-run mode — preview commands without execution
netreaper --dry-run scan 192.168.1.1

# Quick scan
netreaper scan 192.168.1.1

# Full scan (requires root)
sudo netreaper scan 192.168.1.1 --full

# WiFi menu (requires root)
sudo netreaper wifi

# Interactive wizard
netreaper wizard scan

# Configuration
netreaper config path
netreaper config edit

# Non-interactive CI example
NR_NON_INTERACTIVE=1 netreaper status

# Unsafe mode for automated testing
NR_NON_INTERACTIVE=1 NR_UNSAFE_MODE=1 NR_AUTO_AUTHORIZE_NON_INTERACTIVE=1 \
  sudo netreaper scan 192.168.1.0/24

# Force dangerous confirmation in CI (without full unsafe mode)
NR_NON_INTERACTIVE=1 NR_FORCE_DANGEROUS=1 \
  sudo netreaper stress 192.168.1.1

# Menu selection in CI
NR_NON_INTERACTIVE=1 NR_NON_INTERACTIVE_DEFAULT_INDEX=0 \
  netreaper wizard scan
```

---

## Testing & QA

### Running Tests

```bash
# BATS tests (requires bats-core)
NR_NON_INTERACTIVE=1 bats tests/*.bats

# Smoke tests
./tests/smoke/test_help.sh
./tests/smoke/test_version.sh
```

### Test Coverage

| Test File | Coverage |
|-----------|----------|
| `tests/cli.bats` | CLI flags, commands, exit codes |
| `tests/help.bats` | Help output validation |
| `tests/syntax.bats` | Shell syntax checking |
| `tests/detection.bats` | System/distro detection, tool search paths, package name mappings (14 tests for empty args, path list, and mappings) |
| `tests/config.bats` | Configuration persistence, commands, non-interactive behavior |
| `tests/smoke/*.sh` | Quick smoke tests for CI |

### Verification Command

To verify all tests pass:

```bash
NR_NON_INTERACTIVE=1 bats tests/*.bats
```

Expected output: **109 tests, 0 failures**

---

## Legal & License

```
Copyright (c) 2025 Nerds489
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

### Authorized Testing Only

**NETREAPER is designed for authorized security testing only.**

By using this software, you acknowledge that:

- You have **written authorization** to test target systems
- You accept **full legal responsibility** for your actions
- Unauthorized access to computer systems is a **federal crime**

The authors and contributors are not responsible for misuse of this software.

---

## Project History

NETREAPER began as a personal toolkit for streamlining penetration testing workflows. What started as a collection of wrapper scripts evolved into a full-featured framework with:

- **Phase 1: Core refactoring** — Modular `lib`/`bin`/`modules` architecture, centralized version handling
- **Phase 2: Safety & confirmations** — Target validation, authorization model, non-interactive CI support
- **Phase 3: Core infrastructure** — Tool management, progress indicators, persistent configuration, CI correctness

The project follows a "batteries included" philosophy: one CLI to rule all your security tools, with safety guardrails that don't get in your way.

---

## Support

- **Issues:** https://github.com/Nerds489/NETREAPER/issues
- **Discussions:** https://github.com/Nerds489/NETREAPER/discussions
- **Documentation:** See `docs/` directory for HOWTO, QUICKREF, and TROUBLESHOOTING guides

---

<p align="center">
  <strong>NETREAPER</strong> — "Some tools scan. Some tools attack. I do both."
</p>
<p align="center">
  © 2025 Nerds489
</p>
