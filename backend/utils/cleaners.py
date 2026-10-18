"""
Module: cleaners.py
Purpose: Utility functions for cleaning and normalizing raw data values.
Expected: Ensure all returned values are JSON-safe.
"""

import math

def safe_convert(val):
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val