# NetReaper Android Remote Controller

This project provides a comprehensive Android application that serves as a fully functional remote controller for NetReaper, replicating its GUI and enabling secure remote control over network scanning and analysis operations.

## Features

- **Exact GUI Replication**: Matches NetReaper's cyberpunk-themed interface with tabs for SCAN, RECON, WIRELESS, and WEB.
- **Secure Remote Control**: Uses WebSocket over HTTPS for real-time command execution and output streaming.
- **Authentication & Encryption**: JWT-based auth with TLS 1.3 encryption.
- **Offline Capabilities**: Caches recent scans for offline viewing.
- **Performance Optimized**: Supports API 21+, various screen sizes, orientations.
- **Accessibility**: TalkBack support, gesture navigation.

## Architecture

### Server Component (PC)
- **Language**: Python with FastAPI
- **Features**: WebSocket server, command execution, JWT auth, TLS encryption
- **Location**: `server/`

### Android App
- **Language**: Kotlin with Jetpack Compose
- **Features**: UI replication, Ktor WebSocket client, Room caching
- **Location**: `android_app/`

## Setup Instructions

### PC Server Setup

1. Install Python dependencies:
   ```bash
   cd server
   pip install -r requirements.txt
   ```

2. Generate SSL certificates:
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```

3. Run the server:
   ```bash
   python main.py
   ```
   Server runs on https://localhost:8443

### Android App Build

1. Ensure Android Studio with Kotlin and Compose support.

2. Open `android_app` as project.

3. Build APK:
   ```bash
   ./gradlew assembleRelease
   ```

4. Install APK on device.

## Usage

1. Start NetReaper server on PC.

2. Launch Android app.

3. Enter PC IP, password ("netreaper123").

4. Connect and use tabs to execute commands remotely.

## User Guide

- **Connection**: Enter host IP and password in app settings.
- **Tabs**: Switch between SCAN, RECON, etc., enter targets, click buttons.
- **Output**: Real-time log in bottom panel.
- **Offline**: View cached results without connection.

## Command Categories (Android Remote)

The Android controller mirrors NetReaper’s CLI categories so you can trigger every CREDENTIALS, EXPLOIT, and RECON workflow from your device with the same safeguards and automation.

### CREDENTIALS

- **Hashcat workflows** – Load `.hc22000` or `.hash` captures, pick wordlists, monitor status updates, and stream potfile/crack statistics as GPU jobs run.
- **Aircrack-ng** – Point to captured `.cap` files, supply ESSID/BSSID overrides, and evaluate candidate passphrases directly from the app.
- **Hydra/John** – Launch brute-force sessions against HTTP, SMB, FTP, and more with adjustable credential lists, then see authentication responses in real time.
- **Conversion helpers** – Push `.cap` → `.hc22000` conversions (hcxtools/hcxpcapngtool), manage potfiles, and keep capture artifacts synchronized.

### EXPLOIT

- **Frameworks (Metasploit, MSFVenom)** – Start msfconsole snippets, generate payloads with chosen listeners, and transfer payloads for later deployment.
- **Searchsploit** – Run repository queries by keyword, review exploit summaries, and copy payload references straight into the remote terminal.
- **SQL Injection (SQLmap, Commix)** – Provide parameterized URLs, select techniques, and stream vulnerability/extraction output.
- **Web scanners (Nikto, Nuclei, XSStrike)** – Target hosts/URLs with templates, capture findings, and dispatch follow-up recon or attacks without switching contexts.
- **Directory brute-force (Gobuster, Dirb, Feroxbuster)** – Select wordlists, configure recursion, and display discovered paths and response codes.

### RECON

- **Port scanning** – Launch Quick, Full, Stealth, UDP, Vulnerability, and Service-detection scans via presets or custom drop-down options (Nmap/rustscan/masscan).
- **Discovery sweeps** – Execute ping sweeps, Netdiscover/ARP scans, and ICMP sweeps with CIDR input plus live host lists for follow-up.
- **DNS enumeration** – Run `dnsenum`, `dnsrecon`, or zone transfers; catalog DNS records and tag domains for later exploit steps.
- **SSL/TLS and fingerprinting** – Execute `sslscan`, `sslyze`, and `nmap -sV/-O`, then examine cipher suites and cert info on the phone screen.
- **SNMP/SMB enumeration** – Trigger `onesixtyone`, `enum4linux`, and SMB share discovery, stream credential hints, and pivot to cracking workflows when useful.

Each section exposes the same blacklisted/whitelisted target validation and dry-run previews as the desktop tool so the remote experience stays consistent.

## Pairing & Connection Experience

- **Pairing buttons** — The remote app now exposes pairing buttons for both the Android device and the desktop GUI. Tap “Pair Device”/“Pair GUI” after entering the host and password to register each endpoint with the server’s `/pair` API.
- **Automatic pairing logic** — Pairing requests are secured over HTTPS and return an 8-character code that the UI displays immediately; repeated taps refresh the handshake so every phone and GUI instance can stay in sync.
- **Connection indicators** — A dedicated pairing panel shows the WebSocket connection state (connected/connecting/disconnected) with color-coded badges, and logs pairing feedback and connection changes, so you instantly know when a device loses signal.
- **Compatibility** — Works across modern Android devices (API 21+) because it uses standard Ktor/HTTP APIs with TLS and keeps the layout responsive even on large screens or tablets.

## Compatibility

- **PC OS**: Windows, macOS, Linux
- **NetReaper Version**: 6.3.4+
- **Android**: API 21+

## Security Notes

- Use strong passwords.
- Accept self-signed certs on Android (for demo).
- No root required on Android.

## Source Code

- Server: `server/main.py`
- Android: `android_app/`

## License

Apache 2.0
