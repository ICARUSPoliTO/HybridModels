"""
Data Structures for Application State

Contains dataclasses for configuration, optimization, and mission data.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List


@dataclass
class ConfigurationData:
    """Data structure for configuration page inputs"""
    inputs: Dict[str, Any]
    dropdowns: Dict[str, str]
    selected_fuels: List[str]
    fuel_weight_entries: Dict[str, float]
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class OptimizationData:
    """Data structure for optimization page inputs"""
    parameter_points: int
    dport_dt_min: float
    dport_dt_max: float
    dinj_dt_min: float
    dinj_dt_max: float
    lc_dt_min: float
    lc_dt_max: float
    ptank: float
    ttank: float
    pamb: float
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class MissionData:
    """
    Data structure for mission parameters
    
    This is a template - add your mission-specific fields here when ready.
    Example fields:
    - burn_time: float
    - target_altitude: float
    - payload_mass: float
    - flight_profile: str
    """
    pass  # Will be implemented when you add the mission page
