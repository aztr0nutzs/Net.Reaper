#!/usr/bin/env python3
"""
NetReaper GUI — Cyberpunk dark native toolkit interface.

Reimplements the CLI SCAN, RECON, WIRELESS, and WEB flows using PyQt6 so the
toolset is fully usable from a windowed interface without losing the Brass
hammer controls that security engineers expect.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from typing import Iterable, List, Optional, Tuple

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)


CYBER_THEME = """
QWidget {
    background: #050510;
    color: #c9d1ff;
    font-family: "Roboto Mono", "Fira Code", monospace;
}
QTabWidget::pane {
    border: 1px solid #1f1a3d;
    margin-top: -1px;
}
QTabBar::tab {
    background: #0e0b1f;
    padding: 8px 18px;
    border: 1px solid #1f1a3d;
    border-bottom: none;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1c1c5a, stop:1 #4b00ff);
    color: white;
}
QGroupBox {
    border: 1px solid #2a1f63;
    border-radius: 6px;
    margin-top: 10px;
    padding: 12px;
}
QPushButton {
    background: #4c02a0;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
    color: white;
}
QPushButton:hover {
    background: #6c34ff;
}
QComboBox, QLineEdit {
    background: #0f0c1f;
    border: 1px solid #312162;
    padding: 4px;
}
QToolBar {
    background: #080617;
    border: none;
}
QFrame#glowPanel {
    border: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #562dff, stop:1 #00c6ff);
    border-radius: 14px;
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #060513, stop:1 #0d0a1f);
}
QWidget#hudPanel {
    border: 1px solid #5c00ff;
    border-radius: 10px;
    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #090b1d, stop:1 #151438);
}
QLabel#hudLabel {
    font-size: 13px;
    letter-spacing: 1px;
}
QListWidget {
    background: #04050d;
    border: 1px solid #2b1f52;
    border-left: 4px solid #6f00ff;
}
QListWidget::item:selected {
    background: #1e1a38;
}
QPlainTextEdit {
    background: #03030a;
    border: 1px solid #1f1a3d;
    border-left: 4px solid #00c6ff;
}
"""


class CommandThread(QThread):
    """Runs a shell command and emits its output line by line."""

    output = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, command: str):
        super().__init__()
        self.command = command

    def run(self) -> None:
        try:
            process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                executable="/bin/bash",
            )
        except (FileNotFoundError, OSError) as exc:
            self.output.emit(f"[error] {exc}")
            self.finished.emit(1)
            return

        assert process.stdout
        for line in iter(process.stdout.readline, ""):
            self.output.emit(line.rstrip())
        process.stdout.close()
        return_code = process.wait()
        self.finished.emit(return_code)


def quote(value: Optional[str]) -> str:
    if value is None:
        return ""
    return shlex.quote(value.strip())


def apply_glow_effect(widget: QWidget, color: str = "#7c5dff") -> None:
    """Add a pulsating glow effect via drop shadow animation."""

    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(14)
    effect.setColor(QColor(color))
    effect.setOffset(0)
    widget.setGraphicsEffect(effect)

    animation = QPropertyAnimation(effect, b"blurRadius", widget)
    animation.setStartValue(10)
    animation.setEndValue(32)
    animation.setDuration(2100)
    animation.setLoopCount(-1)
    animation.setEasingCurve(QEasingCurve.InOutQuad)
    animation.start()
    widget._glow_animation = animation


def create_glowing_button(text: str, callback) -> QPushButton:
    button = QPushButton(text)
    button.clicked.connect(lambda checked=False, cb=callback: cb())
    apply_glow_effect(button, color="#c87bff")
    return button


class HUDPanel(QWidget):
    """Animated HUD panel that shows status pulses and accent colors."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("hudPanel")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(16)

        self.status_label = QLabel("GRID STATUS: STANDBY")
        self.status_label.setObjectName("hudLabel")
        self.pulse_label = QLabel("Cyber Pulse: 0%")
        self.pulse_label.setObjectName("hudLabel")
        self.latency_label = QLabel("Latency: 10 ms")
        self.latency_label.setObjectName("hudLabel")

        layout.addWidget(self.status_label)
        layout.addWidget(self.pulse_label)
        layout.addStretch()
        layout.addWidget(self.latency_label)

        self._hue = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_hud)
        self._timer.start(220)

        apply_glow_effect(self, color="#5dffeb")

    def _update_hud(self) -> None:
        self._hue = (self._hue + 8) % 360
        pulse = 30 + (self._hue % 70)
        latency = 8 + (self._hue % 40)
        color = QColor.fromHsl(self._hue, 220, 120).name()
        for label in (self.status_label, self.pulse_label, self.latency_label):
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.pulse_label.setText(f"Cyber Pulse: {pulse}%")
        self.latency_label.setText(f"Latency: {latency} ms")


class TargetField(QWidget):
    """Reusable target selector with editable combo box."""

    def __init__(self, label: str, parent: Optional[QWidget] = None, *, share_history: bool = True):
        super().__init__(parent)
        self._history: List[str] = []
        self.share_history = share_history

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(label))

        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        layout.addWidget(self.combo)

    def set_history(self, entries: Iterable[str]) -> None:
        self._history = list(dict.fromkeys(entries))
        current = self.combo.currentText()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(self._history)
        self.combo.setCurrentText(current)
        self.combo.blockSignals(False)

    def value(self) -> str:
        return self.combo.currentText().strip()


class CategoryTab(QWidget):
    """Base tab that wraps command execution hooks."""

    def __init__(self, executor, parent=None):
        super().__init__(parent)
        self.executor = executor
        self.main_window = parent
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(14)
        self.layout.setContentsMargins(4, 4, 4, 4)

    def add_group(self, title: str, description: str) -> QGroupBox:
        group = QGroupBox(title)
        box_layout = QVBoxLayout(group)
        box_layout.setSpacing(8)
        if description:
            info = QLabel(description)
            info.setWordWrap(True)
            box_layout.addWidget(info)
        self.layout.addWidget(group)
        return group


class ScanTab(CategoryTab):
    """SCAN tab with all port scanning options."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.main_window = main_window
        self.target_field = TargetField("Target")
        self.layout.addWidget(self.target_field)
        self.main_window.register_target_field(self.target_field)

        self.scan_presets = {
            "Quick scan (-T4 -F)": self.run_quick,
            "Full scan (-sS -sV -sC -A -p-)": self.run_full,
            "Stealth scan (-sS -T2 -f)": self.run_stealth,
            "UDP scan (-sU --top-ports)": self.run_udp,
            "Vuln scan (--script vuln)": self.run_vuln,
        }

        self.layout.addWidget(self.build_preset_group())
        self.layout.addWidget(self.build_quick_scan_group())
        self.layout.addWidget(self.build_mass_group())
        self.layout.addStretch()

    def build_preset_group(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(QLabel("Preset"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(self.scan_presets.keys()))
        layout.addWidget(self.preset_combo)
        layout.addWidget(create_glowing_button("Launch selected preset", self.run_selected_preset))
        layout.addStretch()
        return container

    def build_quick_scan_group(self) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(8)

        grid.addWidget(QLabel("Run a quick TCP scan across common ports."), 0, 0, 1, 2)
        quick_button = create_glowing_button("Quick scan (nmap -T4 -F)", self.run_quick)
        grid.addWidget(quick_button, 1, 0)

        full_button = create_glowing_button("Full scan (-sS -sV -A -p-)", self.run_full)
        grid.addWidget(full_button, 1, 1)

        stealth_button = create_glowing_button("Stealth (-sS -T2 -f)", self.run_stealth)
        grid.addWidget(stealth_button, 2, 0)

        udp_button = create_glowing_button("UDP scan (--top-ports 100)", self.run_udp)
        grid.addWidget(udp_button, 2, 1)

        vuln_button = create_glowing_button("Vuln scan (--script vuln)", self.run_vuln)
        grid.addWidget(vuln_button, 3, 0)

        service_button = create_glowing_button("Service detection (-sV)", self.run_service)
        grid.addWidget(service_button, 3, 1)

        return container

    def build_mass_group(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(QLabel("Specialized scans"))

        masscan_btn = create_glowing_button("Masscan (fast ports)", self.run_masscan)
        layout.addWidget(masscan_btn)

        rustscan_btn = create_glowing_button("Rustscan + nmap", self.run_rustscan)
        layout.addWidget(rustscan_btn)

        layout.addStretch()
        return container

    def run_selected_preset(self) -> None:
        choice = self.preset_combo.currentText()
        runner = self.scan_presets.get(choice)
        if runner:
            runner()

    def validate_target(self) -> Optional[str]:
        value = self.target_field.value()
        if not value:
            QMessageBox.warning(self, "Target missing", "Enter a target before running scans.")
            return None
        return value

    def run_quick(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"nmap -T4 -F {quote(target)}"
        self.executor(cmd, "Quick scan", target=target)

    def run_full(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"sudo nmap -sS -sV -sC -A -p- {quote(target)}"
        self.executor(cmd, "Full scan", target=target)

    def run_stealth(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"sudo nmap -sS -T2 -f {quote(target)}"
        self.executor(cmd, "Stealth scan", target=target)

    def run_udp(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"sudo nmap -sU --top-ports 100 {quote(target)}"
        self.executor(cmd, "UDP scan", target=target)

    def run_vuln(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"nmap --script vuln {quote(target)}"
        self.executor(cmd, "Vuln scan", target=target)

    def run_service(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"nmap -sV {quote(target)}"
        self.executor(cmd, "Service scan", target=target)

    def run_masscan(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"sudo masscan -p1-65535 {quote(target)} --rate 10000"
        self.executor(cmd, "Masscan sweep", target=target)

    def run_rustscan(self) -> None:
        target = self.validate_target()
        if not target:
            return
        cmd = f"rustscan -a {quote(target)} --ulimit 5000 -- -sV"
        self.executor(cmd, "Rustscan belt", target=target)


class ReconTab(CategoryTab):
    """RECON tab covering discovery and enumeration."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.target_field = TargetField("Subnet/host")
        self.layout.addWidget(self.target_field)
        main_window.register_target_field(self.target_field)
        self.discovery_options = [
            ("Ping sweep (nmap -sn)", "nmap -sn {target}", "Ping sweep"),
            ("Netdiscover", "sudo netdiscover -r {target}", "Netdiscover"),
            ("ARP scan (arp-scan -l)", "sudo arp-scan -l", "ARP scan"),
        ]
        self.enum_options = [
            ("DNS enum (dnsenum)", "dnsenum {target}", "DNS enumeration"),
            ("DNS recon (dnsrecon)", "dnsrecon -d {target}", "DNS recon"),
            ("SSL scan (sslscan)", "sslscan {target}", "SSL scan"),
            ("SSLyze (sslyze)", "sslyze --regular {target}", "SSLyze"),
            ("SNMP sweep (onesixtyone)", "onesixtyone {target}", "SNMP sweep"),
            ("SMB enum (enum4linux)", "enum4linux -a {target}", "SMB enumeration"),
        ]
        self.layout.addWidget(self.create_discovery_group())
        self.layout.addWidget(self.create_enum_group())
        self.layout.addStretch()

    def create_discovery_group(self) -> QGroupBox:
        group = self.add_group("Network Discovery", "ARP, ping, and discovery scans.")
        btn_layout = QGridLayout()
        btn_layout.setSpacing(6)

        for idx, (label, template, desc) in enumerate(self.discovery_options):
            button = create_glowing_button(
                label, lambda template=template, desc=desc: self.run_discovery(template, desc)
            )
            btn_layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(btn_layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Quick discovery selection"))
        self.discovery_combo = QComboBox()
        self.discovery_combo.addItems([label for label, *_ in self.discovery_options])
        drop_layout.addWidget(self.discovery_combo)
        drop_layout.addWidget(create_glowing_button("Execute", self.run_discovery_dropdown))
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        return group

    def create_enum_group(self) -> QGroupBox:
        group = self.add_group("Enumeration", "DNS, SSL/TLS, SNMP, and SMB mapping.")
        layout = QGridLayout()

        for idx, (label, template, desc) in enumerate(self.enum_options):
            button = create_glowing_button(
                label, lambda template=template, desc=desc: self.run_enum(template, desc)
            )
            layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Enumeration quick-run"))
        self.enum_combo = QComboBox()
        self.enum_combo.addItems([label for label, *_ in self.enum_options])
        drop_layout.addWidget(self.enum_combo)
        drop_layout.addWidget(create_glowing_button("Run", self.run_enum_dropdown))
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        return group

    def run_discovery(self, template: str, description: str) -> None:
        target = self.target_field.value()
        if "target" in template and not target:
            QMessageBox.warning(self, "Target missing", "Provide an IP/host/CIDR.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target or "broadcast")

    def run_enum(self, template: str, description: str) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a DNS name or host.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target)

    def run_discovery_dropdown(self) -> None:
        idx = self.discovery_combo.currentIndex()
        if idx < 0:
            return
        _, template, desc = self.discovery_options[idx]
        self.run_discovery(template, desc)

    def run_enum_dropdown(self) -> None:
        idx = self.enum_combo.currentIndex()
        if idx < 0:
            return
        _, template, desc = self.enum_options[idx]
        self.run_enum(template, desc)


class WirelessTab(CategoryTab):
    """WIRELESS tab for interface control, reconnaissance, and cracking."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.executor = executor
        self.iface_field = TargetField("Wireless interface", share_history=False)
        self.layout.addWidget(self.iface_field)
        main_window.register_target_field(self.iface_field)
        self.bssid_field = TargetField("Target BSSID", share_history=False)
        self.layout.addWidget(self.bssid_field)
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Channel")
        self.attack_combo = QComboBox()
        self.attack_combo.addItems(
            ["Deauth attack", "WPS attack (reaver)", "Handshake capture"]
        )
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("Channel"))
        channel_layout.addWidget(self.channel_input)
        self.layout.addLayout(channel_layout)
        self.layout.addWidget(self.build_interface_group())
        self.layout.addWidget(self.build_recon_group())
        self.layout.addWidget(self.build_attacks_group())
        self.layout.addWidget(self.build_cracking_group())
        self.layout.addStretch()

    def build_interface_group(self) -> QGroupBox:
        group = self.add_group("Interface control", "")
        layout = QHBoxLayout()
        enable_btn = create_glowing_button("Enable monitor mode", self.enable_monitor)
        disable_btn = create_glowing_button("Disable monitor mode", self.disable_monitor)
        refresh_btn = create_glowing_button("Refresh interfaces", self.refresh_interfaces)
        layout.addWidget(enable_btn)
        layout.addWidget(disable_btn)
        layout.addWidget(refresh_btn)
        group.layout().addLayout(layout)
        return group

    def build_recon_group(self) -> QGroupBox:
        group = self.add_group("Recon & capture", "airodump-ng, bettercap, wifite.")
        layout = QHBoxLayout()
        airodump = create_glowing_button("Run airodump-ng (10s)", self.run_airodump)
        bettercap = create_glowing_button("Bettercap capture", self.run_bettercap)
        wifite = create_glowing_button("Start wifite (auto)", self.run_wifite)
        layout.addWidget(airodump)
        layout.addWidget(bettercap)
        layout.addWidget(wifite)
        group.layout().addLayout(layout)
        return group

    def build_attacks_group(self) -> QGroupBox:
        group = self.add_group("Attacks", "Deauth, WPS, and handshake capture.")
        layout = QGridLayout()
        deauth_btn = create_glowing_button("Deauth attack", self.deauth_attack)
        wps_btn = create_glowing_button("WPS attack (reaver)", self.wps_attack)
        handshake_btn = create_glowing_button("Capture handshake", self.capture_handshake)
        layout.addWidget(deauth_btn, 0, 0)
        layout.addWidget(wps_btn, 0, 1)
        layout.addWidget(handshake_btn, 1, 0, 1, 2)
        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Attack preset"))
        drop_layout.addWidget(self.attack_combo)
        drop_layout.addWidget(create_glowing_button("Launch attack", self.run_selected_wireless_attack))
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        return group

    def build_cracking_group(self) -> QGroupBox:
        group = self.add_group("Cracking & conversion", "Aircrack-ng / Hashcat helpers.")
        layout = QHBoxLayout()
        aircrack_btn = create_glowing_button("Crack with aircrack-ng", self.run_aircrack)
        hashcat_btn = create_glowing_button("Crack with hashcat", self.run_hashcat)
        convert_btn = create_glowing_button("Convert .cap → .hc22000", self.convert_handshake)
        layout.addWidget(aircrack_btn)
        layout.addWidget(hashcat_btn)
        layout.addWidget(convert_btn)
        group.layout().addLayout(layout)
        return group

    def iface(self) -> Optional[str]:
        value = self.iface_field.value()
        if not value:
            QMessageBox.warning(self, "Interface missing", "Select a wireless interface.")
            return None
        return value

    def refresh_interfaces(self) -> None:
        cmd = "iw dev | awk '/Interface/ {print $2}'"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            executable="/bin/bash",
        )
        interfaces = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if interfaces:
            self.iface_field.combo.clear()
            self.iface_field.combo.addItems(interfaces)
        summary = ", ".join(interfaces) if interfaces else "no wireless interfaces detected"
        if self.main_window:
            self.main_window.output_log.appendPlainText(f"[info] Interfaces refreshed: {summary}")

    def enable_monitor(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo airmon-ng start {quote(iface)}"
        self.executor(cmd, "Enable monitor mode", target=iface)

    def disable_monitor(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo airmon-ng stop {quote(iface)}"
        self.executor(cmd, "Disable monitor", target=iface)

    def run_airodump(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo timeout 15 airodump-ng {quote(iface)}"
        self.executor(cmd, "airodump-ng scan", target=iface)

    def run_bettercap(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo bettercap -iface {quote(iface)} -eval 'set arp.spoof.fullduplex true; net.sniff on'"
        self.executor(cmd, "Bettercap session", target=iface)

    def run_wifite(self) -> None:
        iface = self.iface()
        if not iface:
            return
        cmd = f"sudo wifite -i {quote(iface)} --kill"
        self.executor(cmd, "Wifite attack", target=iface)

    def deauth_attack(self) -> None:
        iface = self.iface()
        if not iface:
            return
        target = self.bssid_field.value() or "FF:FF:FF:FF:FF:FF"
        cmd = f"sudo aireplay-ng --deauth 10 -a {quote(target)} {quote(iface)}"
        self.executor(cmd, "Deauth", target=iface)

    def wps_attack(self) -> None:
        iface = self.iface()
        if not iface:
            return
        target = self.bssid_field.value() or ""
        if not target:
            QMessageBox.warning(self, "BSSID required", "Provide a target BSSID for WPS attacks.")
            return
        channel = self.channel_input.text().strip()
        channel_arg = f"-c {quote(channel)}" if channel else ""
        cmd = f"sudo reaver -i {quote(iface)} -b {quote(target)} {channel_arg} -N -vv"
        self.executor(cmd, "WPS attack (reaver)", target=target)

    def capture_handshake(self) -> None:
        iface = self.iface()
        if not iface:
            return
        target = self.bssid_field.value()
        if not target:
            QMessageBox.warning(self, "BSSID missing", "Provide the target BSSID for capture.")
            return
        channel = self.channel_input.text().strip()
        channel_arg = f"--channel {quote(channel)}" if channel else ""
        cmd = f"sudo timeout 20 airodump-ng --bssid {quote(target)} {channel_arg} -w /tmp/handshake {quote(iface)}"
        self.executor(cmd, "Handshake capture", target=target)

    def run_aircrack(self) -> None:
        capfile, ok = self.request_input("Capture file (.cap)", "/tmp/capture.cap")
        if not ok or not capfile:
            return
        wordlist, _ = self.request_input("Wordlist", "/usr/share/wordlists/rockyou.txt")
        cmd = f"aircrack-ng -w {quote(wordlist)} {quote(capfile)}"
        self.executor(cmd, "Aircrack-ng", target=capfile)

    def run_hashcat(self) -> None:
        hashfile, ok = self.request_input("Hash/Capture file", "/tmp/hash.hc22000")
        if not ok or not hashfile:
            return
        wordlist, _ = self.request_input("Wordlist", "/usr/share/wordlists/rockyou.txt")
        cmd = f"hashcat -m 22000 -a 0 {quote(hashfile)} {quote(wordlist)} --status --potfile-path /tmp/hashcat.pot"
        self.executor(cmd, "Hashcat", target=hashfile)

    def convert_handshake(self) -> None:
        capfile, ok = self.request_input("Capture file (.cap)", "/tmp/handshake.cap")
        if not ok or not capfile:
            return
        cmd = f"hcxpcapngtool -o {quote(capfile)}.hc22000 {quote(capfile)}"
        self.executor(cmd, "Convert handshake", target=capfile)

    def run_selected_wireless_attack(self) -> None:
        choice = self.attack_combo.currentText()
        if choice == "Deauth attack":
            self.deauth_attack()
        elif choice == "WPS attack (reaver)":
            self.wps_attack()
        elif choice == "Handshake capture":
            self.capture_handshake()

    def request_input(self, prompt: str, default: str = "") -> Tuple[str, bool]:
        value, ok = QInputDialog.getText(self, "Input required", prompt, text=default)
        return value, ok


class WebTab(CategoryTab):
    """WEB tab for scanners and injection tools."""

    def __init__(self, executor, main_window):
        super().__init__(executor, main_window)
        self.target_field = TargetField("URL / Domain")
        self.layout.addWidget(self.target_field)
        main_window.register_target_field(self.target_field)
        self.web_scanners = [
            ("SQLmap", "sqlmap -u {target} --batch", "SQL injection"),
            ("Nikto", "nikto -host {target}", "Web server vuln scan"),
            ("Nuclei", "nuclei -u {target}", "Template-based scans"),
            ("XSStrike", "xsstrike {target}", "XSS fuzzing"),
            ("Commix", "commix -u {target} --batch", "Command injection"),
        ]
        self.dir_tools = [
            ("Gobuster", "gobuster dir -u {target} -w /usr/share/wordlists/raft.txt"),
            ("Dirb", "dirb {target} /usr/share/wordlists/raft.txt"),
            ("Feroxbuster", "feroxbuster -u {target} -w /usr/share/wordlists/raft.txt"),
        ]
        self.layout.addWidget(self.build_web_tools_group())
        self.layout.addWidget(self.build_directory_group())
        self.layout.addStretch()

    def build_web_tools_group(self) -> QGroupBox:
        group = self.add_group("Scanners & injection", "SQLmap, Nikto, nuclei, Commix, XSStrike.")
        layout = QGridLayout()

        for idx, (label, template, desc) in enumerate(self.web_scanners):
            button = create_glowing_button(label, lambda t=template, d=desc: self.run_web_tool(t, d))
            layout.addWidget(button, idx // 2, idx % 2)

        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Select scanner"))
        self.web_combo = QComboBox()
        self.web_combo.addItems([label for label, *_ in self.web_scanners])
        drop_layout.addWidget(self.web_combo)
        drop_layout.addWidget(create_glowing_button("Launch", self.run_web_combo))
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        return group

    def build_directory_group(self) -> QGroupBox:
        group = self.add_group("Directory brute-force", "Gobuster, Dirb, Feroxbuster.")
        layout = QHBoxLayout()
        for label, template in self.dir_tools:
            button = create_glowing_button(label, lambda t=template: self.run_dir_tool(t))
            layout.addWidget(button)
        group.layout().addLayout(layout)
        drop_layout = QHBoxLayout()
        drop_layout.addWidget(QLabel("Directory fuzz"))
        self.dir_combo = QComboBox()
        self.dir_combo.addItems([label for label, *_ in self.dir_tools])
        drop_layout.addWidget(self.dir_combo)
        drop_layout.addWidget(create_glowing_button("Start", self.run_dir_combo))
        drop_layout.addStretch()
        group.layout().addLayout(drop_layout)
        return group

    def run_web_tool(self, template: str, description: str) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a URL before running.")
            return
        command = template.format(target=quote(target))
        self.executor(command, description, target=target)

    def run_dir_tool(self, template: str) -> None:
        target = self.target_field.value()
        if not target:
            QMessageBox.warning(self, "Target missing", "Provide a target URL.")
            return
        command = template.format(target=quote(target))
        self.executor(command, "Directory bruteforce", target=target)

    def run_web_combo(self) -> None:
        idx = self.web_combo.currentIndex()
        if idx < 0:
            return
        _, template, desc = self.web_scanners[idx]
        self.run_web_tool(template, desc)

    def run_dir_combo(self) -> None:
        idx = self.dir_combo.currentIndex()
        if idx < 0:
            return
        _, template = self.dir_tools[idx]
        self.run_dir_tool(template)


class NetReaperGui(QWidget):
    """Main container that stitches tabs, logs, and history."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NetReaper GUI")
        self.setMinimumSize(1200, 720)
        self.target_fields: List[TargetField] = []
        self.target_history: List[str] = []
        self.active_threads: List[CommandThread] = []

        main_layout = QVBoxLayout(self)
        self.toolbar = QToolBar("Actions")
        clear_log_action = QAction("Clear log", self)
        clear_log_action.triggered.connect(self.clear_log)
        self.toolbar.addAction(clear_log_action)
        self.toolbar.addSeparator()
        refresh_status_action = QAction("Show status", self)
        refresh_status_action.triggered.connect(lambda: self.execute_command("netreaper status", "Status"))
        self.toolbar.addAction(refresh_status_action)
        main_layout.addWidget(self.toolbar)

        hud = HUDPanel()
        main_layout.addWidget(hud)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        central_frame = QFrame()
        central_frame.setObjectName("glowPanel")
        central_layout = QVBoxLayout(central_frame)
        central_layout.setContentsMargins(2, 2, 2, 2)
        central_layout.addWidget(self.tab_widget)
        apply_glow_effect(central_frame, color="#5c33ff")
        apply_glow_effect(self.tab_widget, color="#00c6ff")
        main_layout.addWidget(central_frame, stretch=3)

        self.output_log = QPlainTextEdit()
        self.output_log.setReadOnly(True)
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.replay_command)

        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        bottom_splitter.addWidget(self.output_log)
        bottom_splitter.addWidget(self.history_list)
        bottom_splitter.setStretchFactor(0, 3)
        bottom_splitter.setStretchFactor(1, 1)
        main_layout.addWidget(bottom_splitter, stretch=2)

        self.scan_tab = ScanTab(self.execute_command, self)
        self.recon_tab = ReconTab(self.execute_command, self)
        self.wireless_tab = WirelessTab(self.execute_command, self)
        self.web_tab = WebTab(self.execute_command, self)
        self.tab_widget.addTab(self.scan_tab, "SCAN")
        self.tab_widget.addTab(self.recon_tab, "RECON")
        self.tab_widget.addTab(self.wireless_tab, "WIRELESS")
        self.tab_widget.addTab(self.web_tab, "WEB")

    def register_target_field(self, field: TargetField) -> None:
        if not field.share_history:
            return
        if field not in self.target_fields:
            self.target_fields.append(field)
            field.set_history([entry for entry in (field.value(),) if entry])

    def add_target_history(self, target: str) -> None:
        if not target:
            return
        history = [target] + [t for t in self.target_history if t != target]
        self.target_history = history[:20]
        for field in self.target_fields:
            field.set_history(history)

    def execute_command(self, command: str, description: str, target: Optional[str] = None) -> None:
        self.output_log.appendPlainText(f"[{description}] $ {command}")
        if target:
            self.add_target_history(target)
        thread = CommandThread(command)
        thread.output.connect(self.output_log.appendPlainText)
        thread.finished.connect(self.on_finished)
        thread.finished.connect(lambda _: self.resize_log())
        self.active_threads.append(thread)
        thread.finished.connect(lambda code, thr=thread: self.cleanup_thread(thr))
        thread.start()

        item = QListWidgetItem(f"{description}: {command}")
        item.setData(Qt.ItemDataRole.UserRole, command)
        self.history_list.addItem(item)

    def cleanup_thread(self, thread: CommandThread) -> None:
        if thread in self.active_threads:
            self.active_threads.remove(thread)

    def on_finished(self, return_code: int) -> None:
        self.output_log.appendPlainText(f"[status] Return code: {return_code}\n")

    def clear_log(self) -> None:
        self.output_log.clear()

    def resize_log(self) -> None:
        cursor = self.output_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output_log.setTextCursor(cursor)

    def replay_command(self, item: QListWidgetItem) -> None:
        command = item.data(Qt.ItemDataRole.UserRole)
        if command:
            self.execute_command(command, "Re-run")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(CYBER_THEME)
    window = QWidget()
    layout = QVBoxLayout(window)
    gui = NetReaperGui()
    layout.addWidget(gui)
    window.setWindowTitle("NetReaper GUI Launcher")
    window.resize(1280, 840)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
