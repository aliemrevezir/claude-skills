"""
Skill validator for Claude Skills.
Validates YAML frontmatter and markdown structure.
"""

import re
import yaml
from typing import Dict, List, Tuple, Optional


class SkillValidator:
    """Validates Claude Skills SKILL.md files."""
    
    def __init__(self, config: Dict):
        """Initialize validator with configuration rules."""
        self.config = config
        self.validation_rules = config.get('validation', {})
    
    def validate(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate a SKILL.md file content.
        
        Args:
            content: The full SKILL.md file content
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for YAML frontmatter
        if not content.startswith('---'):
            errors.append("File must start with YAML frontmatter (---)")
            return False, errors
        
        # Extract frontmatter and markdown
        try:
            frontmatter, markdown = self._extract_frontmatter(content)
        except Exception as e:
            errors.append(f"Failed to parse frontmatter: {str(e)}")
            return False, errors
        
        # Validate frontmatter
        frontmatter_errors = self._validate_frontmatter(frontmatter)
        errors.extend(frontmatter_errors)
        
        # Validate markdown content
        markdown_errors = self._validate_markdown(markdown)
        errors.extend(markdown_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _extract_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter and markdown content."""
        parts = content.split('---', 2)
        
        if len(parts) < 3:
            raise ValueError("Invalid frontmatter format")
        
        # Parse YAML
        frontmatter_text = parts[1].strip()
        frontmatter = yaml.safe_load(frontmatter_text)
        
        # Get markdown content
        markdown = parts[2].strip()
        
        return frontmatter, markdown
    
    def _validate_frontmatter(self, frontmatter: Dict) -> List[str]:
        """Validate YAML frontmatter fields."""
        errors = []
        
        # Required fields
        if 'name' not in frontmatter:
            errors.append("Missing required field: 'name'")
        else:
            # Validate name format
            name = frontmatter['name']
            max_length = self.validation_rules.get('max_name_length', 64)
            pattern = self.validation_rules.get('name_pattern', r'^[a-z0-9-]+$')
            
            if len(name) > max_length:
                errors.append(f"Name exceeds maximum length of {max_length} characters")
            
            if not re.match(pattern, name):
                errors.append(
                    f"Name must contain only lowercase letters, numbers, and hyphens. Got: '{name}'"
                )
        
        if 'description' not in frontmatter:
            errors.append("Missing required field: 'description'")
        else:
            # Validate description length
            description = frontmatter['description']
            min_length = self.validation_rules.get('min_description_length', 20)
            max_length = self.validation_rules.get('max_description_length', 1024)
            
            if len(description) < min_length:
                errors.append(
                    f"Description too short (minimum {min_length} characters). "
                    "A good description helps Claude know when to use the skill."
                )
            
            if len(description) > max_length:
                errors.append(f"Description exceeds maximum length of {max_length} characters")
        
        # Validate optional fields if present
        if 'allowed-tools' in frontmatter:
            allowed_tools = frontmatter['allowed-tools']
            if not isinstance(allowed_tools, (str, list)):
                errors.append("'allowed-tools' must be a string or list")
        
        if 'context' in frontmatter:
            context = frontmatter['context']
            if context not in ['fork']:
                errors.append("'context' must be 'fork' if specified")
        
        if 'user-invocable' in frontmatter:
            user_invocable = frontmatter['user-invocable']
            if not isinstance(user_invocable, bool):
                errors.append("'user-invocable' must be a boolean (true/false)")
        
        return errors
    
    def _validate_markdown(self, markdown: str) -> List[str]:
        """Validate markdown content."""
        errors = []
        
        # Check if markdown is not empty
        if not markdown or len(markdown.strip()) < 50:
            errors.append(
                "Markdown content is too short. "
                "Skills should include clear instructions and examples."
            )
        
        # Check for at least one heading
        if not re.search(r'^#{1,6}\s+.+', markdown, re.MULTILINE):
            errors.append(
                "Markdown should include at least one heading to structure the content"
            )
        
        return errors
    
    def get_frontmatter(self, content: str) -> Optional[Dict]:
        """Extract and return frontmatter as dictionary."""
        try:
            frontmatter, _ = self._extract_frontmatter(content)
            return frontmatter
        except:
            return None
