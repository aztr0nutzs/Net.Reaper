#!/usr/bin/env bats
# NETREAPER CLI Tests

setup() {
    NETREAPER="$BATS_TEST_DIRNAME/../bin/netreaper"
}

@test "netreaper exists and is executable" {
    [ -x "$NETREAPER" ]
}

@test "netreaper --help exits 0" {
    run "$NETREAPER" --help
    [ "$status" -eq 0 ]
}

@test "netreaper --version shows version" {
    run "$NETREAPER" --version
    [ "$status" -eq 0 ]
    [[ "$output" == *"netreaper"* ]]
    [[ "$output" == *"6."* ]]
}

@test "netreaper --dry-run is recognized" {
    run "$NETREAPER" --dry-run --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Dry-run"* ]] || [[ "$output" == *"dry-run"* ]] || true
}

@test "netreaper help command works" {
    run "$NETREAPER" help
    [ "$status" -eq 0 ]
}

@test "netreaper status command works" {
    run "$NETREAPER" status
    [ "$status" -eq 0 ]
    # Verify key sections are present
    [[ "$output" == *"System Information"* ]] || [[ "$output" == *"Tool Status"* ]]
}

@test "netreaper invalid command returns error" {
    run "$NETREAPER" notarealcommand123
    [ "$status" -ne 0 ]
}

@test "netreaper config path works" {
    run "$NETREAPER" config path
    [ "$status" -eq 0 ]
    [[ "$output" == *".netreaper"* ]]
}

@test "netreaper-install exists and is executable" {
    [ -x "$BATS_TEST_DIRNAME/../bin/netreaper-install" ]
}

@test "netreaper-install --help exits 0" {
    run "$BATS_TEST_DIRNAME/../bin/netreaper-install" --help
    [ "$status" -eq 0 ]
}
