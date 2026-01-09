#!/usr/bin/env python3
"""Test script to verify skills browser functionality."""

import sys
sys.path.insert(0, '/Users/aliemrevezir/Documents/github/claude-skills')

from skills_browser import SkillsBrowser

# Test skill discovery
browser = SkillsBrowser()
skills = browser.discover_skills()

print(f"Found {len(skills)} skill(s):")
for skill in skills:
    print(f"  - {skill.name}: {skill.description[:60]}...")
    print(f"    Path: {skill.path}")
    print()

if skills:
    print("✓ Skill discovery working correctly")
else:
    print("⚠ No skills found")
