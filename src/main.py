import logging
import threading
import json
import asyncio
from flask_app import app  # Import the Flask app
from modbus_helpers import setup_server_context, run_modbus_server  # Functions for Modbus context and server
import const

# Configure the logger
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

def load_config():
    """
    Load the configuration from the JSON file.
    
    :return: A tuple containing the address, port, server type, and slave ID.
    :raises SystemExit: If the configuration file is not found or cannot be decoded.
    """
    try:
        _logger.info(f"Loading configuration from {const.ADDON_OPT_PATH}")
        with open(const.ADDON_OPT_PATH) as f:
            config = json.load(f)
            addr = config.get("listen_address", "0.0.0.0")
            port = config.get("listen_port", 502)
            server_type = config.get("server_type", "tcp")
            slave_id = config.get("slave_id", 240)
            return addr, port, server_type, slave_id
    except FileNotFoundError:
        _logger.critical(f"Configuration file not found at {const.ADDON_OPT_PATH}")
        exit(1)
    except json.JSONDecodeError:
        _logger.critical(f"Error decoding JSON from the configuration file at {const.ADDON_OPT_PATH}")
        exit(1)

async def main():
    """
    Main function to start the Modbus and Flask servers.
    """
    # Load the configuration
    addr, port, server_type, slave_id = load_config()

    # Set up the Modbus server context
    context = setup_server_context(const.DATASTORE_PATH)

    # Start the Flask server in a separate thread
    server_thread = threading.Thread(target=app.run, kwargs={'host': addr, 'port': port}, daemon=True)
    server_thread.start()
    _logger.info("Flask server started.")

    # Configure the Modbus server address based on the connection type
    if server_type == "tcp":
        server_addr = (addr, port)
    elif server_type == "serial":
        server_addr = addr
    else:
        _logger.critical("Unsupported server type")
        exit(1)

    # Start the Modbus server
    _logger.info(f"Starting Modbus server on {server_type} at {server_addr}")
    await run_modbus_server(context, server_addr, server_type)

if __name__ == "__main__":
    _logger.info("Running the file directly")
    asyncio.run(main())