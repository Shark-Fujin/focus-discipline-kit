#!/bin/bash

# TOTP Generator for Bedtime Enforcer
# This is your "Google Authenticator" equivalent

SECRET_KEY="JBSWY3DPEHPK3PXP"

generate_totp() {
    local secret="$1"
    local time_step=30
    local current_time=$(date +%s)
    local time_counter=$((current_time / time_step))
    local remaining_time=$((time_step - (current_time % time_step)))
    
    # Simplified TOTP generation (for demo purposes)
    # In production, use proper base32 decoding and HMAC-SHA1
    local simple_hash=$(echo -n "${time_counter}${secret}" | shasum -a 256 | cut -c1-6)
    local code=""
    
    # Convert first 6 hex chars to decimal and mod 1000000
    for i in {0..5}; do
        local hex_char=${simple_hash:$i:1}
        case $hex_char in
            a) hex_char=0 ;;
            b) hex_char=1 ;;
            c) hex_char=2 ;;
            d) hex_char=3 ;;
            e) hex_char=4 ;;
            f) hex_char=5 ;;
        esac
        code="${code}${hex_char}"
    done
    
    printf "%06d" $((code % 1000000))
}

echo "🔐 Bedtime Enforcer TOTP Generator"
echo "=================================="
echo
echo "Current TOTP Code: $(generate_totp "$SECRET_KEY")"
echo "Time until next code: $((30 - $(date +%s) % 30)) seconds"
echo
echo "💡 Use this code to disable Bedtime Enforcer"
echo "🔄 Code refreshes every 30 seconds"
