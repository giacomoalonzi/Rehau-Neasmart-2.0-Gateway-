import asyncio
import logging
import threading
import json
from modbus_helpers import setup_server_context, run_modbus_server
from flask_app import app
import const

# Configure the logger
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

def start_modbus_server(context, addr, server_type):
    """
    Start the Modbus server using asyncio.
    
    Args:
        context: The Modbus server context.
        addr: The address to bind the server to.
        server_type: The type of server (e.g., 'tcp' or 'serial').
    """
    asyncio.run(run_modbus_server(context, addr, server_type))

def load_config():
    """
    Load the configuration from the JSON file.
    
    Returns:
        A tuple containing the address, port, server type, and slave ID.
    
    Raises:
        SystemExit: If the configuration file is not found or cannot be decoded.
    """
    try:
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

def main():
    """
    Main function to start the Modbus and Flask servers.
    """
    addr, port, server_type, slave_id = load_config()
    
    # Set up the Modbus server context
    context = setup_server_context(const.DATASTORE_PATH)

    # Start the Flask server in a separate thread
    server_thread = threading.Thread(target=app.run, kwargs={'host': addr}, daemon=True)
    server_thread.start()

    # Configure the server address based on the server type
    if server_type == "tcp":
        addr = (addr, port)
    elif server_type == "serial":
        addr = addr
    else:
        _logger.critical("Unsupported server type")
        exit(1)

    # Start the Modbus server
    start_modbus_server(context, addr, server_type)

if __name__ == "__main__":
    _logger.info("Running the file directly")
    main()