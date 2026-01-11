#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# NETREAPER - Offensive Security Framework
# ═══════════════════════════════════════════════════════════════════════════════
# Copyright (c) 2025 Nerds489
# SPDX-License-Identifier: Apache-2.0
#
# Wireless library: interface detection, monitor mode management, validation
# ═══════════════════════════════════════════════════════════════════════════════

# Prevent multiple sourcing
[[ -n "${_NETREAPER_WIRELESS_LOADED:-}" ]] && return 0
readonly _NETREAPER_WIRELESS_LOADED=1

# Source core library for logging, colors, and sudo helpers
source "${BASH_SOURCE%/*}/core.sh"

#
# NOTE:
# - is_wireless_interface() lives in lib/detection.sh as the single source of truth.
# - This file intentionally does NOT duplicate that function.
#

# Safety: if someone sources lib/wireless.sh directly without detection.sh
if ! declare -F is_wireless_interface >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    source "${NETREAPER_ROOT:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)}/lib/detection.sh" 2>/dev/null || true
fi

#═══════════════════════════════════════════════════════════════════════════════
# WIRELESS INTERFACE DETECTION
#═══════════════════════════════════════════════════════════════════════════════

# is_wireless_interface() is defined in lib/detection.sh (single source of truth)
# The safety source above ensures it's available.

# List all wireless interfaces
# Returns: one interface per line
# Exit: 0 if found, 1 if none
get_wireless_interfaces() {
    local interfaces=()
    local iface

    for iface_path in /sys/class/net/*; do
        iface=$(basename "$iface_path")
        if is_wireless_interface "$iface"; then
            interfaces+=("$iface")
        fi
    done

    if [[ ${#interfaces[@]} -eq 0 ]]; then
        log_warning "No wireless interfaces found"
        return 1
    fi

    printf '%s\n' "${interfaces[@]}"
    return 0
}

#═══════════════════════════════════════════════════════════════════════════════
# INTERFACE VALIDATION
#═══════════════════════════════════════════════════════════════════════════════

# Validate that an interface exists and is wireless
# Args: $1 = interface name
# Returns: 0 if valid wireless interface, 1 otherwise
validate_wireless_interface() {
    local iface="$1"

    # Check for empty argument
    if [[ -z "$iface" ]]; then
        log_error "No interface specified"
        return 1
    fi

    # Check interface exists
    if [[ ! -d "/sys/class/net/$iface" ]]; then
        log_error "Interface '$iface' does not exist"
        return 1
    fi

    # Check if wireless
    if ! is_wireless_interface "$iface"; then
        log_error "'$iface' is not a wireless interface"
        return 1
    fi

    log_success "Interface $iface validated"
    return 0
}

#═══════════════════════════════════════════════════════════════════════════════
# MONITOR MODE DETECTION
#═══════════════════════════════════════════════════════════════════════════════

# Check if interface is in monitor mode
# Args: $1 = interface name
# Returns: 0 if monitor mode, 1 if managed/other
# Outputs: colored status line
check_monitor_mode() {
    local iface="$1"
    local mode=""

    # Validate input
    if [[ -z "$iface" ]]; then
        return 1
    fi

    # Check interface exists
    if [[ ! -d "/sys/class/net/$iface" ]]; then
        return 1
    fi

    # Method 1: Try iwconfig (legacy but widely supported)
    if command -v iwconfig &>/dev/null; then
        mode=$(iwconfig "$iface" 2>/dev/null | grep -oP 'Mode:\K\w+' || true)
    fi

    # Method 2: Try iw (modern)
    if [[ -z "$mode" ]] && command -v iw &>/dev/null; then
        mode=$(iw dev "$iface" info 2>/dev/null | awk '/type/ {print $2}' || true)
    fi

    # Evaluate mode
    if [[ "${mode,,}" == "monitor" ]]; then
        echo -e "    ${C_GREEN}[✓]${C_RESET} $iface: ${C_GREEN}MONITOR${C_RESET}"
        return 0
    else
        echo -e "    ${C_YELLOW}[!]${C_RESET} $iface: ${C_YELLOW}MANAGED${C_RESET}"
        return 1
    fi
}

#═══════════════════════════════════════════════════════════════════════════════
# MONITOR MODE MANAGEMENT
#═══════════════════════════════════════════════════════════════════════════════

# Enable monitor mode on interface
# Args: $1 = interface name
# Returns: 0 on success, 1 on failure
# Outputs: resulting interface name (may be iface or ifacemon)
enable_monitor_mode() {
    local iface="$1"

    # Validate interface
    if ! validate_wireless_interface "$iface"; then
        return 1
    fi

    # Check if already in monitor mode
    if check_monitor_mode "$iface" &>/dev/null; then
        echo "$iface"
        return 0
    fi

    log_info "Enabling monitor mode on $iface..."

    # Method 1: Try airmon-ng (preferred - handles interfering processes)
    if command -v airmon-ng &>/dev/null; then
        # Kill interfering processes
        run_with_sudo airmon-ng check kill &>/dev/null || true

        # Start monitor mode
        run_with_sudo airmon-ng start "$iface" &>/dev/null || true

        # Check for renamed interface (e.g., wlan0mon)
        if [[ -d "/sys/class/net/${iface}mon" ]]; then
            if check_monitor_mode "${iface}mon" &>/dev/null; then
                echo "${iface}mon"
                return 0
            fi
        fi

        # Check if original interface is now in monitor mode
        if check_monitor_mode "$iface" &>/dev/null; then
            echo "$iface"
            return 0
        fi
    fi

    # Method 2: Manual fallback using ip/iw
    run_with_sudo ip link set "$iface" down 2>/dev/null || true
    run_with_sudo iw dev "$iface" set type monitor 2>/dev/null || true
    run_with_sudo ip link set "$iface" up 2>/dev/null || true

    # Verify monitor mode enabled
    if check_monitor_mode "$iface" &>/dev/null; then
        echo "$iface"
        return 0
    fi

    log_error "Failed to enable monitor mode on $iface"
    return 1
}

# Disable monitor mode on interface
# Args: $1 = interface name (could be iface or ifacemon)
# Returns: 0 on success (always succeeds with best effort)
disable_monitor_mode() {
    local iface="$1"

    if [[ -z "$iface" ]]; then
        log_error "No interface specified"
        return 1
    fi

    log_info "Disabling monitor mode on $iface..."

    # Method 1: Try airmon-ng (handles renamed interfaces)
    if command -v airmon-ng &>/dev/null; then
        run_with_sudo airmon-ng stop "$iface" &>/dev/null || true
    fi

    # Method 2: Manual fallback - always attempt
    run_with_sudo ip link set "$iface" down 2>/dev/null || true
    run_with_sudo iw dev "$iface" set type managed 2>/dev/null || true
    run_with_sudo ip link set "$iface" up 2>/dev/null || true

    # Restart NetworkManager if running (best effort)
    if command -v systemctl &>/dev/null; then
        if systemctl is-active --quiet NetworkManager 2>/dev/null; then
            run_with_sudo systemctl restart NetworkManager &>/dev/null || true
        fi
    fi

    log_success "Monitor mode disabled"
    return 0
}

#═══════════════════════════════════════════════════════════════════════════════
# EXPORTS
#═══════════════════════════════════════════════════════════════════════════════

export -f is_wireless_interface
export -f get_wireless_interfaces
export -f validate_wireless_interface
export -f check_monitor_mode
export -f enable_monitor_mode
export -f disable_monitor_mode


#═══════════════════════════════════════════════════════════════════════════════
# WIFI DISCOVERY (JSON EXPORT)
#═══════════════════════════════════════════════════════════════════════════════

# Escape a string for safe JSON emission (minimal, but handles quotes/backslashes/newlines)
_json_escape() {
    local s="${1:-}"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

# WiFi scan -> JSON file (for visualization / reporting)
#
# NOTE:
# - This is intended for *authorized* environments you own or have permission to assess.
# - Uses nmcli when available (no monitor mode required), else falls back to iw (root).
#
# Args:
#   $1 = interface (optional; auto-detects first wireless iface if empty)
#   $2 = output json path (optional; defaults to $OUTPUT_DIR/wifi_scan_latest.json)
#
# Output JSON schema:
#   {
#     "generated_at":"ISO8601",
#     "iface":"wlan0",
#     "backend":"nmcli|iw",
#     "networks":[{"bssid":..,"ssid":..,"channel":..,"freq_mhz":..,"signal":..,"security":..}, ...]
#   }
wifi_scan_json() {
    local iface="${1:-}"
    local out_path="${2:-${OUTPUT_DIR}/wifi_scan_latest.json}"

    # If iface omitted, choose first wireless interface.
    if [[ -z "$iface" ]]; then
        iface="$(get_wireless_interfaces 2>/dev/null | head -n 1 || true)"
    fi

    if [[ -z "$iface" ]]; then
        log_error "No wireless interface available"
        return 1
    fi

    # Validate the interface exists + is wireless (does not require monitor mode)
    validate_wireless_interface "$iface" || true

    mkdir -p "$(dirname "$out_path")" 2>/dev/null || true

    # Check cache (5 minutes)
    local cache_dir="${HOME}/.netreaper/cache"
    mkdir -p "$cache_dir" 2>/dev/null || true
    local cache_file="${cache_dir}/wifi_scan_$(echo "$iface" | md5sum | cut -d' ' -f1).json"
    if [[ -f "$cache_file" && $(find "$cache_file" -mmin -5 2>/dev/null) ]]; then
        log_info "Using cached WiFi scan for $iface"
        cp "$cache_file" "$out_path" 2>/dev/null || true
        return 0
    fi

    local iso_ts
    iso_ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    local backend=""
    local tmp
    tmp="$(mktemp -t netreaper_wifi_scan_XXXXXX)" || return 1

    # Preferred: nmcli (stable + easy parse)
    if check_tool "nmcli"; then
        backend="nmcli"

        # nmcli output is per-AP; use a safe separator
        # Fields:
        #  BSSID | SSID | CHAN | FREQ | SIGNAL | SECURITY
        # SIGNAL is typically 0..100 (percent)
        nmcli -t --separator '|' -f BSSID,SSID,CHAN,FREQ,SIGNAL,SECURITY dev wifi list ifname "$iface" --rescan yes 2>/dev/null >"$tmp" || true

        if [[ ! -s "$tmp" ]]; then
            # If nmcli can't scan (e.g., iface in monitor mode), fall back to iw.
            backend=""
        fi
    fi

    if [[ -z "$backend" ]]; then
        if ! check_tool "iw"; then
            rm -f "$tmp" 2>/dev/null || true
            log_error "Missing tools: need 'nmcli' or 'iw' for WiFi discovery"
            return 1
        fi
        require_root "WiFi discovery scan (iw)" || { rm -f "$tmp" 2>/dev/null || true; return 1; }
        backend="iw"

        # iw scan parsing is best-effort; SSIDs may be empty/hidden
        iw dev "$iface" scan 2>/dev/null >"$tmp" || true
    fi

    # Emit JSON
    {
        printf '{\n'
        printf '  "generated_at": "%s",\n' "$(_json_escape "$iso_ts")"
        printf '  "iface": "%s",\n' "$(_json_escape "$iface")"
        printf '  "backend": "%s",\n' "$(_json_escape "$backend")"
        printf '  "networks": [\n'

        local first=1

        if [[ "$backend" == "nmcli" ]]; then
            while IFS='|' read -r bssid ssid chan freq signal security; do
                [[ -z "${bssid:-}" ]] && continue
                [[ "$first" -eq 0 ]] && printf ',\n'
                first=0

                # Normalize
                ssid="${ssid:-}"
                chan="${chan:-0}"
                freq="${freq:-0}"
                signal="${signal:-0}"
                security="${security:-}"

                printf '    {'
                printf '"bssid":"%s",' "$(_json_escape "$bssid")"
                printf '"ssid":"%s",' "$(_json_escape "$ssid")"
                printf '"channel":%s,' "${chan:-0}"
                printf '"freq_mhz":%s,' "${freq:-0}"
                printf '"signal":%s,' "${signal:-0}"
                printf '"security":"%s"' "$(_json_escape "$security")"
                printf '}'
            done <"$tmp"
        else
            # iw best-effort parser
            local bssid="" ssid="" freq="0" chan="0" signal="" security=""
            while IFS= read -r line; do
                # New BSS record
                if [[ "$line" =~ ^BSS[[:space:]]+([0-9A-Fa-f:]{17}) ]]; then
                    # flush previous
                    if [[ -n "$bssid" ]]; then
                        [[ "$first" -eq 0 ]] && printf ',\n'
                        first=0
                        printf '    {'
                        printf '"bssid":"%s",' "$(_json_escape "$bssid")"
                        printf '"ssid":"%s",' "$(_json_escape "$ssid")"
                        printf '"channel":%s,' "${chan:-0}"
                        printf '"freq_mhz":%s,' "${freq:-0}"
                        if [[ -n "$signal" ]]; then
                            printf '"signal":%s,' "$signal"
                        else
                            printf '"signal":0,'
                        fi
                        printf '"security":"%s"' "$(_json_escape "$security")"
                        printf '}'
                    fi
                    bssid="${BASH_REMATCH[1]}"
                    ssid=""
                    freq="0"
                    chan="0"
                    signal=""
                    security=""
                    continue
                fi

                # SSID:
                if [[ "$line" =~ ^[[:space:]]*SSID:[[:space:]]*(.*)$ ]]; then
                    ssid="${BASH_REMATCH[1]}"
                    continue
                fi

                # freq:
                if [[ "$line" =~ ^[[:space:]]*freq:[[:space:]]*([0-9]+) ]]; then
                    freq="${BASH_REMATCH[1]}"
                    # crude channel mapping for 2.4/5 (best effort)
                    if [[ "$freq" -ge 2412 && "$freq" -le 2484 ]]; then
                        chan=$(( (freq - 2407) / 5 ))
                    elif [[ "$freq" -ge 5000 && "$freq" -le 5900 ]]; then
                        chan=$(( (freq - 5000) / 5 ))
                    fi
                    continue
                fi

                # signal:
                if [[ "$line" =~ ^[[:space:]]*signal:[[:space:]]*([-0-9]+\.[0-9]+)[[:space:]]*dBm ]]; then
                    # store as negative number (dBm), but keep numeric
                    signal="${BASH_REMATCH[1]}"
                    continue
                fi

                # RSN/WPA:
                if [[ "$line" =~ RSN: ]]; then
                    security="RSN"
                    continue
                fi
                if [[ "$line" =~ WPA: ]]; then
                    security="WPA"
                    continue
                fi
            done <"$tmp"

            # flush last record
            if [[ -n "$bssid" ]]; then
                [[ "$first" -eq 0 ]] && printf ',\n'
                first=0
                printf '    {'
                printf '"bssid":"%s",' "$(_json_escape "$bssid")"
                printf '"ssid":"%s",' "$(_json_escape "$ssid")"
                printf '"channel":%s,' "${chan:-0}"
                printf '"freq_mhz":%s,' "${freq:-0}"
                if [[ -n "$signal" ]]; then
                    printf '"signal":%s,' "$signal"
                else
                    printf '"signal":0,'
                fi
                printf '"security":"%s"' "$(_json_escape "$security")"
                printf '}'
            fi
        fi

        printf '\n  ]\n'
        printf '}\n'
    } >"$out_path"

    rm -f "$tmp" 2>/dev/null || true

    # Save to cache
    cp "$out_path" "$cache_file" 2>/dev/null || true

    log_success "WiFi discovery JSON saved: $out_path"
    return 0
}

