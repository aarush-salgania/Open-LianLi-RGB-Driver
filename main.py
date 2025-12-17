import usb.core
import usb.util
import os
import sys
import json
import argparse

# --- Configuration & Constants ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# Default Packet Header for Lian Li (Used only if config is missing)
DEFAULT_PACKET_HEADER = "018500000014030400"
DEFAULT_PACKET_FOOTER = "00000000000000000000000000180000000000000000000000000000000000000000000000000000000000000000000000000000"


def load_config():
    """Loads settings from JSON. Returns empty dict if no file exists."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Config file is corrupted. Starting fresh.")
    return {}


def save_config(vid, pid, endpoint=2, header=DEFAULT_PACKET_HEADER, footer=DEFAULT_PACKET_FOOTER):
    """Saves the working configuration to file."""
    data = {
        "vid": vid,
        "pid": pid,
        "endpoint": endpoint,
        "packet_header": header,
        "packet_footer": footer
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Configuration saved to {CONFIG_FILE}")


# --- USB Controller Logic ---
class RGBDevice:
    def __init__(self, vid, pid, endpoint):
        # Convert hex strings to int if necessary
        self.vid = int(vid, 16) if isinstance(vid, str) else vid
        self.pid = int(pid, 16) if isinstance(pid, str) else pid
        self.endpoint = endpoint
        self.dev = None
        self.connect()

    def connect(self):
        self.dev = usb.core.find(idVendor=self.vid, idProduct=self.pid)
        if self.dev is None:
            raise ValueError(f"Device VID:{hex(self.vid)} PID:{hex(self.pid)} not found. Please check connection.")
        self.dev.set_configuration()

    def send_color_packet(self, hex_color, header, footer):
        """Constructs and sends the raw hex packet."""
        hex_color = hex_color.replace("#", "").lower()
        full_payload = header + hex_color + footer

        try:
            packet_data = bytes.fromhex(full_payload)
        except ValueError:
            raise ValueError("Invalid Hex Data. Check config header/footer or color code.")

        try:
            if self.dev:
                self.dev.write(self.endpoint, packet_data)
                return True
        except usb.core.USBError:
            # Try reconnecting once
            try:
                self.connect()
                self.dev.write(self.endpoint, packet_data)
                return True
            except Exception as e:
                print(f"Failed to send packet: {e}")
        return False


# --- CLI Tools ---
def scan_devices():
    """Prints all connected USB devices."""
    print(f"{'VID':<10} {'PID':<10} {'Product Name'}")
    print("-" * 50)
    devices = usb.core.find(find_all=True)
    count = 0
    for dev in devices:
        try:
            vid = hex(dev.idVendor)
            pid = hex(dev.idProduct)
            product = usb.util.get_string(dev, dev.iProduct) if dev.iProduct else "Unknown"
            print(f"{vid:<10} {pid:<10} {product}")
            count += 1
        except:
            pass
    if count == 0:
        print("No devices found or permission denied (Try running as Admin).")


def manual_set_color(args):
    """Sets color and saves config if successful."""
    config = load_config()

    # Priority: CLI Args > Config File > Fail
    vid = args.vid if args.vid else config.get("vid")
    pid = args.pid if args.pid else config.get("pid")

    # Validation
    if not vid or not pid:
        print("Error: VID and PID are missing.")
        print("Usage first time: python main.py set <color> --vid <vid> --pid <pid>")
        print("Run 'python main.py scan' to find your device IDs.")
        return

    endpoint = config.get("endpoint", 2)
    header = config.get("packet_header", DEFAULT_PACKET_HEADER)
    footer = config.get("packet_footer", DEFAULT_PACKET_FOOTER)

    print(f"Connecting to VID:{vid} PID:{pid}...")
    try:
        # Attempt connection
        device = RGBDevice(vid, pid, endpoint)
        success = device.send_color_packet(args.color, header, footer)

        if success:
            print(f"Successfully set color to #{args.color}")
            # Save the known working config so user doesn't need flags next time
            save_config(vid, pid, endpoint, header, footer)
        else:
            print("Device found, but failed to send packet.")
    except Exception as e:
        print(f"Error: {e}")


# --- Main Entry Point ---
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Universal USB RGB Controller")
        print("----------------------------")
        print("Usage:")
        print("  python main.py scan                     -> List all USB devices")
        print("  python main.py set <hex> --vid X --pid Y -> Set color & Save Config")
        print("  python main.py set <hex>                -> Set color using Saved Config")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Universal USB RGB Controller")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Scan Command
    subparsers.add_parser('scan', help='Scan for connected USB devices')

    # Set Color Command
    set_parser = subparsers.add_parser('set', help='Set a static hex color')
    set_parser.add_argument('color', type=str, help='Hex color code (e.g. FF0000)')
    set_parser.add_argument('--vid', type=str, help='Device Vendor ID (e.g. 0x0416)')
    set_parser.add_argument('--pid', type=str, help='Device Product ID (e.g. 0x7399)')

    args = parser.parse_args()

    if args.command == 'scan':
        scan_devices()
    elif args.command == 'set':
        manual_set_color(args)