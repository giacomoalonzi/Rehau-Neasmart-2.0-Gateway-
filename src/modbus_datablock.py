import threading
import os
from pymodbus.datastore import ModbusSequentialDataBlock
from sqlitedict import SqliteDict
import const

class LockingPersistentDataBlock(ModbusSequentialDataBlock):
    """
    A Modbus data block that uses a lock to ensure thread-safe access and 
    persists data using SqliteDict.
    """
    def __init__(self, address, values):
        """
        Initialize the data block with the given address and values.
        
        :param address: The starting address of the data block.
        :param values: The initial values of the data block.
        """
        super().__init__(address, values)
        self.lock = threading.Lock()  # Lock for thread-safe access
        self.reg_dict = None  # Dictionary to persist register values

    def setValues(self, address, value):
        """
        Set the values in the data block at the given address.
        
        :param address: The starting address to set the values.
        :param value: The values to set.
        """
        with self.lock:
            if not isinstance(value, list):
                value = [value]
            for k in range(len(value)):
                self.reg_dict[address + k] = value[k]  # Persist the value
            super().setValues(address, value)  # Call the parent method

    def getValues(self, address, count=1):
        """
        Get the values from the data block starting at the given address.
        
        :param address: The starting address to get the values.
        :param count: The number of values to get.
        :return: The values from the data block.
        """
        with self.lock:
            return super().getValues(address, count=count)  # Call the parent method

    @classmethod
    def create_lpdb(cls, reg_datastore_path):
        """
        Create an instance of LockingPersistentDataBlock with data persisted 
        in a SqliteDict.
        
        :param reg_datastore_path: The path to the SQLite database file.
        :return: An instance of LockingPersistentDataBlock.
        """
        # Initialize the SQLite dictionary if it does not exist
        if not os.path.exists(reg_datastore_path):
            init_dict = SqliteDict(reg_datastore_path, tablename=const.SQLITEDICT_REGS_TABLE, autocommit=False)
            for k in range(65536):
                init_dict[k] = 0  # Initialize all registers to 0
            init_dict.commit()
            init_dict.close()
        
        # Open the SQLite dictionary with autocommit enabled
        reg_dict = SqliteDict(reg_datastore_path, tablename=const.SQLITEDICT_REGS_TABLE, autocommit=True)
        sorted_dict = dict(sorted(reg_dict.items(), key=lambda x: int(x[0])))  # Sort the dictionary by key
        instance = cls(const.REGS_STARTING_ADDR, list(sorted_dict.values()))  # Create an instance
        instance.reg_dict = reg_dict  # Assign the SQLite dictionary to the instance
        return instance