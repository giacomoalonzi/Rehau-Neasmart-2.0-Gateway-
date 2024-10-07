from modbus_datablock import LockingPersistentDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.server import StartAsyncSerialServer, StartAsyncTcpServer
from pymodbus.framer import ModbusRtuFramer, ModbusSocketFramer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus import __version__ as pymodbus_version
import const

def setup_server_context(datastore_path):
    """
    Set up the Modbus server context with the given datastore path.
    
    :param datastore_path: The path to the SQLite database file for persistent storage.
    :return: A ModbusServerContext object configured with the slave context.
    """
    # Create a LockingPersistentDataBlock for holding register values
    datablock = LockingPersistentDataBlock.create_lpdb(datastore_path)
    
    # Create a ModbusSlaveContext with different types of data blocks
    slave_context = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*65536),  # Discrete Inputs
        co=ModbusSequentialDataBlock(0, [0]*65536),  # Coils
        hr=datablock,  # Holding Registers
        ir=ModbusSequentialDataBlock(0, [0]*65536),  # Input Registers
        zero_mode=True  # Addressing mode
    )
    
    # Return a ModbusServerContext with the slave context
    return ModbusServerContext(slaves={240: slave_context}, single=False)  # Change slave_id to 240 as default or make it variable

async def run_modbus_server(server_context, server_addr, conn_type):
    """
    Run the Modbus server with the given context, address, and connection type.
    
    :param server_context: The Modbus server context.
    :param server_addr: The address to bind the server to.
    :param conn_type: The type of connection ('tcp' or 'serial').
    """
    # Create a ModbusDeviceIdentification object with server information
    identity = ModbusDeviceIdentification(
        info_name={
            "VendorName": "Pymodbus",
            "ProductCode": "PM",
            "VendorUrl": "https://github.com/pymodbus-dev/pymodbus/",
            "ProductName": "Pymodbus Server",
            "ModelName": "Pymodbus Server",
            "MajorMinorRevision": pymodbus_version,
        }
    )
    
    # Start the Modbus server based on the connection type
    if conn_type == "tcp":
        await StartAsyncTcpServer(context=server_context, identity=identity, address=server_addr, framer=ModbusSocketFramer)
    elif conn_type == "serial":
        await StartAsyncSerialServer(context=server_context, identity=identity, port=server_addr, framer=ModbusRtuFramer)
    else:
        _logger.critical("Unsupported connection type")
        exit(1)