# Changelog

All notable changes to NETREAPER.

## [6.3.4] - 2025-12-13

### Fixed
- **install.sh – Sourcery review fixes**
  - `_verify_installation`: Guard `--version` execution when `wrapper_path` is empty/invalid
  - `_cleanup_legacy`: Relax failure for `--user` installs when system legacy binaries exist but can't be removed (warn-only for non-root)
  - `_do_uninstall`: Proper success/failure tracking with distinct `uninstall_removed_any` and `uninstall_failed_any` flags; exits non-zero on partial failure

### Changed
- Version consistency enforcement across all files (6.3.4 is now the single source of truth)

## [6.3.3] - 2025-12-12

### Added
- **install.sh – Callable Command Guarantee**
  - `_dir_in_path()` helper to check if a directory is in PATH
  - `_select_install_dir()` choosing best install directory (`/usr/local/bin` → `/usr/bin` → fallback with PATH fix)
  - `_create_path_dropin()` to create `/etc/profile.d/netreaper.sh` if needed for PATH augmentation
  - Installer creates wrapper scripts in install directory pointing to `bin/netreaper` and `bin/netreaper-install`
  - Post-install verification **hard-fails** if `command -v netreaper` fails
  - `bin/netreaper-install` only runs if arguments are provided (prevents accidental execution)

- **lib/detection.sh – Tool Detection Fixes**
  - New `TOOL_SEARCH_PATHS` constant covering comprehensive search locations:
    `/usr/bin /usr/local/bin /usr/sbin /usr/local/sbin /sbin /bin /opt/bin ~/.local/bin ~/go/bin`
  - `check_tool()` and `get_tool_path()` now search all directories in `TOOL_SEARCH_PATHS`
  - Empty tool names are rejected (return 1)
  - New `tool_package_name()` function with distro-family mappings:
    - Aircrack suite tools (`aircrack-ng`, `airodump-ng`, `aireplay-ng`, etc.) → `aircrack-ng` package
    - `dig`: debian → `dnsutils`, redhat → `bind-utils`, arch → `bind`
    - `tshark`: debian → `tshark`, redhat/arch → `wireshark-cli`
    - `netcat`: debian → `netcat-openbsd`, redhat → `nmap-ncat`, arch → `openbsd-netcat`
  - `auto_install_tool()` now uses `tool_package_name()` for correct per-distro resolution

- **tests/detection.bats**
  - 14 new tests covering empty args, path list validation, and package name mappings

## [6.3.2] - 2025-12-12

### Fixed
- **CI correctness**: All log output now goes to stderr, preserving stdout for data
- **`config get` output**: Now returns raw values only (no colors, headers, or logging)
- Installer hard-fails if legacy v5.x binaries cannot be removed (prevents broken hybrid state)
- Post-install verification ensures only the modular wrapper is installed

### Changed
- `reinstall-netreaper.sh` rewritten with strict CI safety:
  - Requires explicit confirmation in interactive mode
  - Non-interactive mode requires `NR_NON_INTERACTIVE=1` AND `NR_FORCE_REINSTALL=1`
  - Uses `umask 077` and bash strict mode
  - Verifies `netreaper --version` matches VERSION file after install

### Added
- Environment variables for CI/automation: `NR_FORCE_REINSTALL`, `NR_KEEP_CONFIG`, `NR_REMOVE_CONFIG`

## [6.3.1] - 2025-12-12

### Added
- Protection against legacy v5.x monolithic installs (auto-removed during install)
- Reinstall script (`reinstall-netreaper.sh`) for clean installation

### Changed
- Finalized Phase 3 core infrastructure (tools, progress, config)

## [6.2.4] - 2025-12-10

### Added
- Modular dispatcher architecture (`bin/netreaper` as thin dispatcher)
- Version handling via `lib/version.sh` (single source of truth)
- Centralized logging system with log levels (DEBUG, INFO, SUCCESS, WARNING, ERROR, FATAL)
- File logging to `~/.netreaper/logs/netreaper_YYYYMMDD.log`
- Audit trail logging to `~/.netreaper/logs/audit_YYYYMMDD.log`
- Smart sudo/privilege helpers: `is_root()`, `require_root()`, `run_with_sudo()`, `elevate_if_needed()`, `can_get_root()`
- Target validation system: `is_valid_ip()`, `is_valid_cidr()`, `is_private_ip()`, `is_protected_ip()`, `validate_target()`
- Public IP warnings and authorization checks with `confirm_dangerous()` integration
- Protected IP ranges blocking (loopback, multicast, broadcast, link-local, reserved)
- Confirmation prompts: `confirm()`, `confirm_dangerous()`, `prompt_input()`, `select_option()`
- Input validators: `validate_not_empty()`, `validate_integer()`, `validate_positive_integer()`, `validate_port_range()`
- `NR_UNSAFE_MODE` environment variable to bypass safety checks
- `NR_NON_INTERACTIVE` mode for CI/headless environments
- Dispatcher commands: `--dry-run`, `help`, `config path`
- Unified error-handling framework: `die()`, `assert()`, `try()`, `error_handler()` with stack traces
- Exit code constants: `EXIT_CODE_SUCCESS`, `EXIT_CODE_FAILURE`, `EXIT_CODE_INVALID_ARGS`, `EXIT_CODE_PERMISSION`, `EXIT_CODE_NETWORK`, `EXIT_CODE_TARGET_INVALID`, `EXIT_CODE_TOOL_MISSING`
- Tool checking utilities: `require_tool()`, `check_tool()`, `get_tool_path()`
- Safe file operations: `safe_rm()`, `safe_mkdir()`, `safe_copy()`, `safe_move()` with protected path blocking
- Log utilities: `set_log_level()`, `show_logs()`, `rotate_logs()`, `init_logging()`

### Changed
- `bin/netreaper` refactored into thin dispatcher sourcing modular libs
- Core logic moved into `lib/core.sh`, `lib/ui.sh`, `lib/safety.sh`, `lib/detection.sh`, `lib/utils.sh`
- All scripts now read version and `NETREAPER_ROOT` from `lib/version.sh`
- Improved CI behavior with non-interactive logic (auto-accept prompts, skip wizards)
- `validate_target()` now uses `confirm_dangerous()` for public IP confirmation
- All confirmation/input functions respect `NR_NON_INTERACTIVE` mode
- Enhanced `error_handler()` with stack trace support and audit logging

### Fixed
- Legacy CLI incompatibilities with dispatcher
- Public IP scanning without warnings now properly blocked or confirmed
- `--dry-run` flag not being recognized
- `help` command failing previously
- `config path` command failing previously
- `ORIGINAL_ARGS` unbound variable error with `set -u`
- Inconsistent privilege handling and unclear root requirements
- Lack of audit trail for security-relevant operations

## [6.2.2] - 2025-12-10

### Fixed
- Resolved E2BIG "argument list too long" error when invoking sudo with large argument expansion

## [6.2.1] - 2025-12-09

### Added
- Root-level wrapper binaries (`netreaper`, `netreaper-install`) that forward to the executables in `bin/`, preserving historical `./netreaper` workflows.
- Dedicated Bash, Zsh, and Fish completion scripts in `completions/` plus documentation explaining how to enable them.
- Smoke tests under `tests/smoke/` (`test_help.sh`, `test_version.sh`) that mirror the CI entrypoints.

### Changed
- Repository layout and quickstart docs now highlight the `bin/` directory, wrapper scripts, and the clean root-level structure.
- `install.sh` strictly delegates to `bin/netreaper-install`, and the README/HowTo/Quick Reference call out the wrapper usage.
- Non-interactive detection honors `NR_NON_INTERACTIVE=1` **and** TTY absence, skipping the wizard, legal prompts, and auto-marking `FIRST_RUN_COMPLETE`.

### Fixed
- CI runs without blocking prompts—no more wizard/legal interaction required for headless environments.
- Version reporting is consistent across the CLI, installer, and core libraries (single source of truth via `VERSION`).

### Removed
- Remaining EULA language; Apache 2.0 is now the only license mentioned anywhere.

## [6.2.0] - 2024-12-09

### Added
- `bin/` directory for executables (professional structure)
- `tests/smoke/` directory with smoke tests
- `docs/images/` directory for screenshots
- `--dry-run` flag for safe command preview
- `nr_run()` and `nr_run_eval()` wrapper functions in lib/core.sh
- "First 60 Seconds" quickstart section in README
- "Why NETREAPER?" comparison table in README
- "Dry-Run Mode" documentation in README
- "Project History" section in README
- CI badge in README
- Release workflow (.github/workflows/release.yml)

### Changed
- Moved `netreaper` → `bin/netreaper`
- Moved `netreaper-install` → `bin/netreaper-install`
- `install.sh` is now thin wrapper calling `bin/netreaper-install`
- CI workflow updated for `bin/` structure
- README completely overhauled with landing page style
- Installer version synced to main version (6.2.0)

### Fixed
- uninstall.sh now removes both netreaper and netreaper-install

### Structure
```
bin/
  netreaper           # Main toolkit
  netreaper-install   # Tool installer
lib/                  # Core libraries
modules/              # Feature modules
tests/
  smoke/              # Smoke tests
  *.bats              # Bats tests
docs/
  images/             # Screenshots
install.sh            # System installer (wrapper)
uninstall.sh          # Uninstaller
```

## [6.1.0] - 2024-12-09

### Changed
- **License Clarification**: NETREAPER is 100% Apache 2.0 with no additional restrictions
- Removed EULA directory and all associated acceptance language
- Version standardization: single source of truth from VERSION file
- Code cleanup: added shellcheck disable directives for intentionally exported variables

### Fixed
- ShellCheck warnings properly addressed (not hidden with severity config)
- SC2034: Added explicit directives for exported variables (colors, PKG_*, TOOLS_*)
- Syntax error in first_run_wizard() from empty if-then block
- Version inconsistencies across all script files

### Removed
- `EULA/` directory completely removed
- All EULA/terms acceptance language from scripts
- Unused `term_cmd` variable from netreaper-install

## [6.0.1] - 2024-12-09

### Fixed
- CI test fixes for detection.bats
- Prevented log_to_file from failing in CI environments

## [6.0.0] - 2024-12-09

### Added
- Modular architecture with `lib/` and `modules/` directories
- Authorization flow on first run
- Target validation (blocks dangerous operations by default)
- `NR_UNSAFE_MODE` environment variable for advanced users
- Bats test suite (47 tests)
- GitHub Actions CI with ShellCheck
- `--dry-run` flag for installer

### Changed
- Main script refactored to thin dispatcher
- Installer refactored with clear functions
- Installer version bumped to 3.0.0

### Structure
```
lib/core.sh        - Logging, colors, paths
lib/ui.sh          - Menus, prompts, banners
lib/safety.sh      - Authorization, validation
lib/detection.sh   - Distro/tool detection
lib/utils.sh       - Helper functions

modules/recon.sh       - Network reconnaissance
modules/wireless.sh    - WiFi operations
modules/scanning.sh    - Port scanning
modules/exploit.sh     - Exploitation
modules/credentials.sh - Password cracking
modules/traffic.sh     - Packet analysis
modules/osint.sh       - OSINT gathering
```

## [5.3.1] - 2024-12-08

### Fixed
- Interface validation improvements
- Installer compatibility fixes

## [5.3.0] - 2024-12-07

### Added
- Multi-distro support (Fedora, RHEL, Arch, openSUSE, Alpine)
- Improved wizard mode
- JSON output for status

---

[6.3.4]: https://github.com/Nerds489/NETREAPER/compare/v6.3.3...v6.3.4
[6.3.3]: https://github.com/Nerds489/NETREAPER/compare/v6.3.2...v6.3.3
[6.3.2]: https://github.com/Nerds489/NETREAPER/compare/v6.3.1...v6.3.2
[6.3.1]: https://github.com/Nerds489/NETREAPER/compare/v6.2.4...v6.3.1
[6.2.4]: https://github.com/Nerds489/NETREAPER/compare/v6.2.3...v6.2.4
[6.2.2]: https://github.com/Nerds489/NETREAPER/compare/v6.2.1...v6.2.2
[6.2.1]: https://github.com/Nerds489/NETREAPER/compare/v6.2.0...v6.2.1
[6.2.0]: https://github.com/Nerds489/NETREAPER/releases/tag/v6.2.0
[6.1.0]: https://github.com/Nerds489/NETREAPER/releases/tag/v6.1.0
[6.0.1]: https://github.com/Nerds489/NETREAPER/releases/tag/v6.0.1
[6.0.0]: https://github.com/Nerds489/NETREAPER/releases/tag/v6.0.0
[5.3.1]: https://github.com/Nerds489/NETREAPER/releases/tag/v5.3.1
[5.3.0]: https://github.com/Nerds489/NETREAPER/releases/tag/v5.3.0
