from enum import Enum

class DriveType(str, Enum):
    FWD = "FWD"
    RWD = "RWD"
    AWD = "AWD"
    _4WD = "4WD"
    _4x2 = "4x2"
    UNKNOWN = "UNKNOWN"

class FuelType(str, Enum):
    DIESEL = "DIESEL"
    ELECTRIC = "ELECTRIC"
    FLEXIBLE_FUEL = "FLEXIBLE FUEL"
    GAS = "GAS"
    HYBRID_ENGINE = "HYBRID ENGINE"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"

class Transmission(str, Enum):
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"