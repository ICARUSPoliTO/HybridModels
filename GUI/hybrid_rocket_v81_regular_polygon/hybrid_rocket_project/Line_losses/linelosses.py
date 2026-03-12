"""
This file provides the builder for the feeding line losses model
"""
import numpy as np


# Global variable to store line losses value (set from GUI)
_line_losses_value = 0.0


def set_line_losses(delta_p):
    """Set the line losses value from GUI"""
    global _line_losses_value
    _line_losses_value = float(delta_p)


def linelosses():
    """Return the configured line losses value"""
    global _line_losses_value
    return _line_losses_value
