from .registry import register
from crft.hardware.serial_transport import SerialTransport
from crft.drivers.pn532_hsu import PN532_HSU
from crft.cards.ntag21x import NTAG21x

def register_builtins():
    # Hardware
    register("hardware", "serial", SerialTransport)
    
    # Drivers
    register("driver", "pn532", PN532_HSU)
    
    # Cards (with SAK for auto-detection)
    register("card", "ntag21x", NTAG21x, sak=0x00)

# Execute automatically when this module is imported
register_builtins()
