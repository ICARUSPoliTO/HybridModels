"""
Mission module - Mission simulation and chamber update functions
"""

from .chamber_update import (
    update_Temperature_and_gasproperties,
    update_chamberpressure
)

# Note: mission_simulation imports are complex due to dependencies
# Import directly when needed: from Mission import mission_simulation
