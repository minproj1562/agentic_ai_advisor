# app/core/config.py
"""
Configuration re-export module for backward compatibility.
The actual settings are defined in app/config.py
"""

from app.config import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]