"""
User preferences manager for Claude Skills Generator.
Saves and loads user preferences to avoid repeated questions.
"""

import json
import os
from pathlib import Path
from typing import Optional


class PreferencesManager:
    """Manages user preferences for the skill generator."""
    
    def __init__(self, prefs_file: str = ".claude-skills-prefs.json"):
        """Initialize preferences manager."""
        # Save preferences in project directory
        self.prefs_file = Path(prefs_file)
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> dict:
        """Load preferences from file."""
        if self.prefs_file.exists():
            try:
                with open(self.prefs_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_preferences(self):
        """Save preferences to file."""
        try:
            with open(self.prefs_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            # Silently fail - preferences are not critical
            pass
    
    def get(self, key: str, default=None):
        """Get a preference value."""
        return self.preferences.get(key, default)
    
    def set(self, key: str, value):
        """Set a preference value and save."""
        self.preferences[key] = value
        self._save_preferences()
    
    def get_output_location(self) -> Optional[str]:
        """Get saved output location preference."""
        return self.get('output_location')
    
    def set_output_location(self, location: str):
        """Save output location preference."""
        self.set('output_location', location)
    
    def get_wants_hooks_default(self) -> Optional[bool]:
        """Get saved hooks preference."""
        return self.get('wants_hooks')
    
    def set_wants_hooks_default(self, wants_hooks: bool):
        """Save hooks preference."""
        self.set('wants_hooks', wants_hooks)
