# Universal USB RGB Controller (Reverse Engineered)

A lightweight, open-source Python CLI tool to control USB RGB devices by sending raw hex packets directly to hardware endpoints. 

Designed originally for **Lian Li Uni Fan** controllers, this tool allows you to bypass resource-heavy proprietary software (like L-Connect) and control lighting via command line or automation scripts.

> **⚠️ DISCLAIMER: USE AT YOUR OWN RISK** > This software relies on reverse-engineered USB protocols. Sending incorrect hex packets to hardware endpoints carries a non-zero risk of causing firmware instability, erratic behavior, or in rare cases, **"bricking" the device**.  
> * **No Warranty:** The author is not responsible for any hardware damage, voided warranties, or data loss.  
> * **Interoperability:** This tool is created solely for interoperability purposes.

---

## 🚀 Features

- **Universal Driver:** Works with any USB device if you know the VID/PID and packet structure.
- **Zero-Bloat:** A single Python script (<150 lines) replaces ~500MB+ of vendor software.
- **Auto-Config:** Automatically saves your device details after the first successful connection.
- **Device Scanner:** Built-in utility to scan and identify connected USB hardware.

---

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Windows (Admin privileges required for raw USB access)

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/Universal-USB-RGB-Controller.git](https://github.com/YOUR_USERNAME/Universal-USB-RGB-Controller.git)
cd Universal-USB-RGB-Controller

```

### 2. Install Dependencies

```bash
pip install pyusb

```

*(Note: You may also need to install `libusb-win32` driver for your specific device using [Zadig](https://zadig.akeo.ie/) if Windows prevents raw access, though many devices work out of the box).*

---

## 📖 Usage

### 1. Find your Device

Run the scan command to list all connected USB devices and find your controller's **Vendor ID (VID)** and **Product ID (PID)**.

```bash
python main.py scan

```

*Output Example:*

```text
VID        PID        Product Name
----------------------------------------
0x0416     0x7399     Lian Li Controller
0x046d     0xc077     Logitech Mouse

```

### 2. Set a Color (First Run)

The first time you run the tool, you must provide the VID and PID you found above. This creates a `config.json` file automatically.

```bash
# Set LEDs to RED (FF0000) for Lian Li Controller
python main.py set FF0000 --vid 0x0416 --pid 0x7399

```

### 3. Set a Color (Subsequent Runs)

Once the config is saved, you can simply run:

```bash
python main.py set 00FF00  # Sets to Green
python main.py set 0000FF  # Sets to Blue

```

---

## 🧠 How it Works (Reverse Engineering)

Most RGB controllers function as simple USB HID devices. By analyzing the USB traffic between the official software and the hardware using **Wireshark**, we can isolate the specific "Control Packets."

**The Lian Li Protocol:**
Through packet sniffing, I identified that the controller listens on **Endpoint 0x02**. The color command follows this structure:

| Byte Index | Value (Hex) | Description |
| --- | --- | --- |
| **0-8** | `01 85 00...` | **Header:** Command signature initiating color change. |
| **9-14** | `FF 00 00` | **Payload:** The RGB Hex Color code. |
| **15+** | `00 00...` | **Padding/Footer:** Required null bytes to fill the packet buffer. |

This script manually constructs that byte array and writes it directly to the USB interface using `pyusb`.

---

## 🔧 Configuration

You can manually edit `config.json` (created after first run) to tweak the endpoint or packet structure for other devices.

```json
{
    "vid": "0x0416",
    "pid": "0x7399",
    "endpoint": 2,
    "packet_header": "018500000014030400",
    "packet_footer": "00..."
}

```

## 🤝 Contributing

Pull requests are welcome! If you reverse engineer the protocol for other devices (Corsair, Razer, NZXT), please submit a PR adding their default packet structures to the documentation.

## 📄 License

MIT License

