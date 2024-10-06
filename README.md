
# Rehau Neasmart 2.0 Gateway 

> **Disclaimer**: This version is a porting of the [original version](https://github.com/MatteoManzoni/RehauNeasmart2.0_Gateway) designed as an add-on for Home Assistant on a Docker container for core installations.

## Overview

This codebase provides a bridge between the Rehau Neasmart 2.0 SysBus interface (a variant of Modbus) and Home Assistant through a set of REST APIs. It is intended to be used with a custom integration to expose the Rehau Neasmart 2.0 system as a climate entity within Home Assistant. The Add-On supports persistent storage (approximately 3MB) for register state storage.

## How to Use

1. **Configure Adapter**: Set up your Serial to USB adapter or a ModbusRTU Slave to ModbusTCP adapter. Refer to the [waveshare RS485 TO POE ETH (B) how-to guide](./waveshare_poegw_howto.md) for detailed instructions.
2. **Install Add-On**: Add this add-on repository to your Home Assistant installation.
3. **Configure Add-On**: 
  - Specify the Serial port path or listening address in the `listening_address` field.
  - Set a `listening_port` that matches the ModbusRTU Slave to ModbusTCP adapter configuration.
  - Choose `tcp` or `serial` as the `server_type` (use `serial` if a Serial port is specified in the listening address).
  - Set a `slave_id` (valid IDs are 240 and 241). This add-on can coexist with the KNX GW using a different ID.

## Known Issues

- **Initial Database**: On first startup, the add-on initializes an empty database, resulting in all write registers being zeroed. A change in write registers is required to start displaying those values in reading.
- **Register Updates**: If the add-on is down and changes occur through other means (e.g., app, thermostat), the register won't be updated. On add-on restart, the old value will be re-read through the bus, invalidating the change.
- **Storage Limitations**: SQLITE is not optimal for very slow disks, network disks (if missing `flock()`), and SD Cards (frequent writes can damage them).
- **Flask Development Server**: The add-on uses a Flask development server.
- **API Authentication & Ingress**: The add-on lacks API authentication and ingress support.

