#!/usr/bin/env python3
"""
packet_editor.py
Educational packet editor / forensics tool using Scapy.

Features:
 - Interactive CLI to craft Ethernet/IP/TCP/UDP/ICMP packets
 - Send packet(s) and optionally wait for responses
 - Sniff and list captured packets, show hex, and edit/resend captures
 - Save / load PCAP files
 - Strict safety reminders
"""
import sys
import os
import json
import time
from scapy.all import (
    Ether, IP, TCP, UDP, ICMP, Raw,
    sendp, send, sniff, rdpcap, wrpcap, hexdump, conf
)

# Brief safety check
def safety_notice():
    print("="*72)
    print("PACKET EDITOR — EDUCATIONAL USE ONLY")
    print("Only run this tool on hosts/networks you own or have permission to test.")
    print("Scapy operations often require root. Stopping here if you disagree.")
    print("="*72)
    print()

# Simple interactive builder helpers
def build_packet_interactive():
    print("Choose link layer (1) None (2) Ether")
    link = input("link> ").strip() or "1"
    link_layer = None
    if link == "2":
        src_mac = input("src MAC (enter to skip): ").strip() or None
        dst_mac = input("dst MAC (enter to skip): ").strip() or None
        link_layer = Ether()
        if src_mac: link_layer.src = src_mac
        if dst_mac: link_layer.dst = dst_mac

    # Network layer
    proto = input("Network proto (1) IPv4 (2) none > ").strip() or "1"
    ip_layer = None
    if proto == "1":
        src_ip = input("src IP (default 127.0.0.1)> ").strip() or "127.0.0.1"
        dst_ip = input("dst IP (default 127.0.0.1)> ").strip() or "127.0.0.1"
        ip_layer = IP(src=src_ip, dst=dst_ip)

    # Transport layer
    print("Transport layer (1) TCP (2) UDP (3) ICMP (4) raw/none")
    t = input("transport> ").strip() or "1"
    trans_layer = None
    if t == "1":
        sport = int(input("src port (e.g. 1234)> ").strip() or 1234)
        dport = int(input("dst port (e.g. 80)> ").strip() or 80)
        flags = input("TCP flags (e.g. S for SYN) [enter for none]> ").strip() or None
        trans_layer = TCP(sport=sport, dport=dport)
        if flags: trans_layer.flags = flags
    elif t == "2":
        sport = int(input("src port (e.g. 1234)> ").strip() or 1234)
        dport = int(input("dst port (e.g. 53)> ").strip() or 53)
        trans_layer = UDP(sport=sport, dport=dport)
    elif t == "3":
        trans_layer = ICMP()
    else:
        trans_layer = None

    payload = input("Payload (ascii) [leave empty for none]> ")
    payload_layer = Raw(load=payload.encode()) if payload else None

    # Compose
    pkt = None
    parts = []
    if link_layer: parts.append(link_layer)
    if ip_layer: parts.append(ip_layer)
    if trans_layer: parts.append(trans_layer)
    if payload_layer: parts.append(payload_layer)

    # reduce composition nicely
    pkt = parts[0]
    for p in parts[1:]:
        pkt = pkt / p

    print("\nConstructed packet summary:")
    pkt.show()
    return pkt

# Send packet (link-layer or ip-layer depending)
def send_packet(pkt, iface=None, count=1, wait_for_reply=False, timeout=2):
    print(f"Sending {count} packet(s)...")
    # If packet has an Ether layer, use sendp (L2), otherwise send (L3)
    if Ether in pkt:
        sendp(pkt, iface=iface, count=count, verbose=True)
    else:
        send(pkt, count=count, verbose=True)

    if wait_for_reply:
        # Try a basic sniff with a filter targeted at destination IP
        dst = pkt[IP].dst if IP in pkt else None
        if dst:
            print(f"Listening for replies to {dst} for {timeout}s...")
            replies = sniff(filter=f"host {dst}", timeout=timeout, count=10)
            print(f"Captured {len(replies)} reply packets.")
            for i, r in enumerate(replies):
                print(f"--- reply {i} ---")
                r.summary()
                hexdump(r)
            return replies
    return []

# Sniffing function
def capture_packets(count=10, timeout=5, lfilter=None):
    print(f"Sniffing for up to {timeout}s or {count} packets...")
    pkts = sniff(count=count, timeout=timeout, lfilter=lfilter)
    print(f"Captured {len(pkts)} packets.")
    return pkts

# Hex / dump utilities
def show_packet_hex(pkt):
    hexdump(pkt)

# Save / load pcap helpers
def save_pcap(pkts, filename):
    wrpcap(filename, pkts)
    print(f"Saved {len(pkts)} packet(s) to {filename}")

def load_pcap(filename):
    pkts = rdpcap(filename)
    print(f"Loaded {len(pkts)} packet(s) from {filename}")
    return pkts

# Minimal interactive shell
def repl():
    safety_notice()
    captured = []  # local list of captured packets you can edit/resend
    last_pkt = None
    while True:
        try:
            cmd = input("\npacket-editor> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return
        if not cmd:
            continue

        parts = cmd.split()
        c = parts[0].lower()

        if c in ("quit", "exit"):
            print("bye.")
            return

        elif c == "help":
            print("""Commands:
  build            - interactively craft a packet
  send <n>         - send last-built packet (optional count n). e.g. send 5
  sendfile <pcap>  - send all packets from a pcap file
  sniff [count] [timeout] - capture packets (defaults 10,5)
  list             - list captured packets (index, summary)
  show <i>         - show detailed packet i (Scapy show)
  hex <i>          - display hex of packet i
  edit <i>         - edit payload of packet i (simple ASCII overwrite)
  save <file.pcap> - save captured packets to pcap
  load <file.pcap> - load packets from pcap into captured list
  clear            - clear captured list
  iface <name>     - set outgoing interface (default scapy conf.iface)
  help/quit
""")
        elif c == "build":
            pkt = build_packet_interactive()
            last_pkt = pkt
            print("Packet stored as 'last_pkt'. Use `send` to transmit or `show` to inspect.")

        elif c == "send":
            if last_pkt is None and len(parts) >= 2:
                print("No last-built packet. Use `build` or `load` a pcap.")
                continue
            count = int(parts[1]) if len(parts) >= 2 else 1
            iface = None
            send_packet(last_pkt, iface=iface, count=count)

        elif c == "sendfile" and len(parts) >= 2:
            fname = parts[1]
            if not os.path.exists(fname):
                print("File not found:", fname); continue
            pkts = load_pcap(fname)
            for p in pkts:
                send_packet(p, count=1)
            print("Finished sending pcap packets (one shot).")

        elif c == "sniff":
            cnt = int(parts[1]) if len(parts) >= 2 else 10
            tout = int(parts[2]) if len(parts) >= 3 else 5
            pkts = capture_packets(count=cnt, timeout=tout)
            if pkts:
                captured.extend(pkts)
                last_pkt = pkts[-1]

        elif c == "list":
            for i, p in enumerate(captured):
                print(f"[{i}] {p.summary()}")

        elif c == "show" and len(parts) >= 2:
            i = int(parts[1])
            if 0 <= i < len(captured):
                captured[i].show()
            else:
                print("Index out of range.")

        elif c == "hex" and len(parts) >= 2:
            i = int(parts[1])
            if 0 <= i < len(captured):
                show_packet_hex(captured[i])
            else:
                print("Index out of range.")

        elif c == "edit" and len(parts) >= 2:
            i = int(parts[1])
            if 0 <= i < len(captured):
                pkt = captured[i]
                print("Current payload (if any):")
                if Raw in pkt:
                    try:
                        print(pkt[Raw].load.decode(errors='replace'))
                    except Exception:
                        print(repr(pkt[Raw].load))
                else:
                    print("<no raw payload>")
                new_payload = input("Enter new ASCII payload (empty to cancel)> ")
                if new_payload != "":
                    # simple replace: strip old Raw and attach new one
                    # keep other layers intact
                    layers = []
                    # rebuild layers up to transport
                    cur = pkt
                    while True:
                        layers.append(cur.copy())
                        if Raw in cur:
                            break
                        # attempt to find next layer by / operator; scapy lets you use payload
                        if hasattr(cur, "payload") and cur.payload:
                            cur = cur.payload
                        else:
                            break
                    # remove any Raw layer and append new Raw
                    # quick approach: create new_pkt = pkt.copy(); delete payloads then / Raw(new)
                    new_pkt = pkt.copy()
                    # strip payloads by setting .remove_payload() repeatedly if available
                    try:
                        while new_pkt.payload:
                            new_pkt.remove_payload()
                    except Exception:
                        pass
                    new_pkt = new_pkt / Raw(load=new_payload.encode())
                    captured[i] = new_pkt
                    last_pkt = new_pkt
                    print("Packet payload replaced.")
            else:
                print("Index out of range.")

        elif c == "save" and len(parts) >= 2:
            fname = parts[1]
            if not captured:
                print("No captured packets to save.")
            else:
                save_pcap(captured, fname)

        elif c == "load" and len(parts) >= 2:
            fname = parts[1]
            if not os.path.exists(fname):
                print("File not found.")
            else:
                pkts = load_pcap(fname)
                captured.extend(pkts)
                if pkts:
                    last_pkt = pkts[-1]

        elif c == "clear":
            captured = []
            last_pkt = None
            print("Cleared captured list.")

        elif c == "iface" and len(parts) >= 2:
            iface = parts[1]
            conf.iface = iface
            print("Set scapy iface to", conf.iface)

        else:
            print("Unknown command. Type 'help'.")

if __name__ == "__main__":
    try:
        repl()
    except PermissionError:
        print("Permission error: try running with root/administrator privileges.")
    except Exception as e:
        print("Fatal error:", e)
        raise
