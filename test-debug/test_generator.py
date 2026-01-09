"""
Test script for Claude Skills Generator.
Run basic tests to verify functionality.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_validator import SkillValidator
import yaml


def test_validator():
    """Test the skill validator."""
    print("🧪 Testing Skill Validator...\n")
    
    # Load config
    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    validator = SkillValidator(config)
    
    # Test 1: Valid skill
    valid_skill = """---
name: test-skill
description: This is a test skill that demonstrates proper formatting and validation. Use when testing the skill generator.
---

# Test Skill

This is a test skill with proper structure.

## Instructions

1. Do something
2. Do something else

## Examples

Here's an example of how to use this skill.
"""
    
    is_valid, errors = validator.validate(valid_skill)
    print(f"Test 1 - Valid Skill: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if errors:
        print(f"  Errors: {errors}")
    print()
    
    # Test 2: Missing name
    missing_name = """---
description: A skill without a name
---

# Content
"""
    
    is_valid, errors = validator.validate(missing_name)
    print(f"Test 2 - Missing Name: {'✅ PASS' if not is_valid else '❌ FAIL (should fail)'}")
    if errors:
        print(f"  Expected errors: {errors}")
    print()
    
    # Test 3: Invalid name format
    invalid_name = """---
name: Invalid_Name_With_Underscores
description: This has an invalid name format
---

# Content
"""
    
    is_valid, errors = validator.validate(invalid_name)
    print(f"Test 3 - Invalid Name Format: {'✅ PASS' if not is_valid else '❌ FAIL (should fail)'}")
    if errors:
        print(f"  Expected errors: {errors}")
    print()
    
    # Test 4: Description too short
    short_description = """---
name: test-skill
description: Too short
---

# Content with enough markdown

This has enough content in the markdown section.
"""
    
    is_valid, errors = validator.validate(short_description)
    print(f"Test 4 - Short Description: {'✅ PASS' if not is_valid else '❌ FAIL (should fail)'}")
    if errors:
        print(f"  Expected errors: {errors}")
    print()
    
    # Test 5: Extract frontmatter
    frontmatter = validator.get_frontmatter(valid_skill)
    print(f"Test 5 - Extract Frontmatter: {'✅ PASS' if frontmatter is not None else '❌ FAIL'}")
    if frontmatter:
        print(f"  Name: {frontmatter.get('name')}")
        print(f"  Description: {frontmatter.get('description')[:50]}...")
    print()
    
    print("✨ Validation tests complete!\n")


def test_example_skills():
    """Test example skills in the examples directory."""
    print("🧪 Testing Example Skills...\n")
    
    # Load config
    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    validator = SkillValidator(config)
    
    examples_dir = Path(__file__).parent.parent / 'examples'
    
    if not examples_dir.exists():
        print("No examples directory found, skipping...")
        return
    
    # Find all SKILL.md files
    skill_files = list(examples_dir.rglob('SKILL.md'))
    
    if not skill_files:
        print("No example skills found, skipping...")
        return
    
    for skill_file in skill_files:
        skill_name = skill_file.parent.name
        content = skill_file.read_text()
        
        is_valid, errors = validator.validate(content)
        
        print(f"Example: {skill_name}")
        print(f"  Status: {'✅ Valid' if is_valid else '❌ Invalid'}")
        if errors:
            print(f"  Errors:")
            for error in errors:
                print(f"    - {error}")
        print()
    
    print("✨ Example skills tested!\n")


if __name__ == '__main__':
    print("=" * 60)
    print("Claude Skills Generator - Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_validator()
        test_example_skills()
        
        print("=" * 60)
        print("✅ All tests complete!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
