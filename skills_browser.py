#!/usr/bin/env python3
"""
Claude Skills Browser - Interactive skill browser and importer.

Browse global Claude skills with arrow key navigation and import them
to your project with a single keypress.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Optional
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
import questionary
from questionary import Style

console = Console()

# Visual styling constants
COLORS = {
    'primary': '#4ECDC4',      # Vibrant teal
    'accent': '#FF6B6B',        # Coral red
    'success': '#51CF66',       # Fresh green
    'warning': '#FFD93D',       # Bright yellow
    'info': '#74B9FF',          # Sky blue
    'muted': '#858585',         # Subtle gray
    'header': '#FF6B6B',        # Coral for headers
    'highlight': '#4ECDC4',     # Teal for highlights
}

ICONS = {
    'success': '✓',
    'error': '✗',
    'warning': '⚠',
    'info': 'ℹ',
    'search': '🔍',
    'import': '📦',
    'already_imported': '✔',
    'skill': '🎯',
    'sparkle': '✨',
    'rocket': '🚀',
    'wave': '👋',
}

# Custom style for the interactive browser
custom_style = Style([
    ('qmark', f'fg:{COLORS["primary"]} bold'),
    ('question', 'bold'),
    ('answer', f'fg:{COLORS["accent"]} bold'),
    ('pointer', f'fg:{COLORS["primary"]} bold'),
    ('highlighted', f'fg:{COLORS["highlight"]} bold'),
    ('selected', f'fg:{COLORS["accent"]}'),
    ('separator', f'fg:{COLORS["muted"]}'),
    ('instruction', ''),
    ('text', ''),
    ('disabled', 'fg:#858585 italic')
])


class Skill:
    """Represents a Claude skill."""
    
    def __init__(self, name: str, path: Path, frontmatter: dict):
        self.name = name
        self.path = path
        self.frontmatter = frontmatter
        self.description = frontmatter.get('description', 'No description available')
        self.user_invocable = frontmatter.get('user-invocable', True)
        self.allowed_tools = frontmatter.get('allowed-tools', None)
    
    def __str__(self):
        return f"{self.name} - {self.description[:60]}..."
    
    def get_display_name(self, is_imported=False):
        """Get formatted display name for the list."""
        imported_indicator = f" {ICONS['already_imported']}" if is_imported else ""
        return f"{ICONS['skill']} {self.name}{imported_indicator}"
    
    def get_preview(self, is_imported=False) -> str:
        """Get detailed preview of the skill."""
        from rich.markdown import Markdown
        from rich.table import Table
        
        # Build the preview with rich formatting
        output = []
        
        # Title with icon
        output.append(f"[bold {COLORS['header']}]{ICONS['skill']} {self.name}[/bold {COLORS['header']}]")
        output.append("")
        
        # Status badges
        badges = []
        if self.user_invocable:
            badges.append(f"[{COLORS['success']}]{ICONS['success']} User Invocable[/{COLORS['success']}]")
        else:
            badges.append(f"[{COLORS['muted']}]⊘ Not User Invocable[/{COLORS['muted']}]")
        
        if is_imported:
            badges.append(f"[{COLORS['info']}]{ICONS['already_imported']} Already Imported[/{COLORS['info']}]")
        
        if self.allowed_tools:
            badges.append(f"[{COLORS['warning']}]{ICONS['info']} Tool Restricted[/{COLORS['warning']}]")
        
        output.append(" • ".join(badges))
        output.append("")
        
        # Description section
        output.append(f"[bold {COLORS['primary']}]Description[/bold {COLORS['primary']}]")
        # Truncate long descriptions intelligently
        desc = self.description
        if len(desc) > 300:
            desc = desc[:297] + "..."
        output.append(desc)
        output.append("")
        
        # Tool restrictions (if any)
        if self.allowed_tools:
            output.append(f"[bold {COLORS['primary']}]Allowed Tools[/bold {COLORS['primary']}]")
            if isinstance(self.allowed_tools, list):
                tool_pills = [f"[{COLORS['accent']}]▪ {tool}[/{COLORS['accent']}]" for tool in self.allowed_tools]
                output.append(", ".join(tool_pills))
            else:
                output.append(str(self.allowed_tools))
            output.append("")
        
        # Metadata footer
        output.append("─" * 60)
        try:
            skill_file = self.path / "SKILL.md"
            if skill_file.exists():
                size_bytes = skill_file.stat().st_size
                size_kb = size_bytes / 1024
                output.append(f"[{COLORS['muted']}]📁 {self.path} • 📄 {size_kb:.1f} KB[/{COLORS['muted']}]")
            else:
                output.append(f"[{COLORS['muted']}]📁 {self.path}[/{COLORS['muted']}]")
        except:
            output.append(f"[{COLORS['muted']}]📁 {self.path}[/{COLORS['muted']}]")
        
        return "\n".join(output)


class SkillsBrowser:
    """Browser for discovering and importing Claude skills."""
    
    def __init__(self):
        self.global_skills_dir = Path.home() / ".claude" / "skills"
        self.project_skills_dir = Path(".claude") / "skills"
        self.skills: List[Skill] = []
        self.imported_skills: set = set()  # Track which skills are already imported
    
    def is_skill_imported(self, skill: Skill) -> bool:
        """Check if a skill is already imported in the project."""
        dest_path = self.project_skills_dir / skill.name
        return dest_path.exists()
    
    def update_imported_skills(self):
        """Update the set of imported skills."""
        self.imported_skills.clear()
        if self.project_skills_dir.exists():
            for skill in self.skills:
                if self.is_skill_imported(skill):
                    self.imported_skills.add(skill.name)
    
    def discover_skills(self) -> List[Skill]:
        """Discover all skills in the global directory."""
        skills = []
        
        if not self.global_skills_dir.exists():
            console.print(f"[{COLORS['warning']}]{ICONS['warning']} Global skills directory not found: {self.global_skills_dir}[/{COLORS['warning']}]")
            console.print(f"[{COLORS['info']}]{ICONS['info']} Creating directory...[/{COLORS['info']}]")
            self.global_skills_dir.mkdir(parents=True, exist_ok=True)
            return skills
        
        # Find all SKILL.md files
        for skill_dir in self.global_skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            
            # Parse frontmatter
            try:
                content = skill_file.read_text()
                frontmatter = self._extract_frontmatter(content)
                
                if frontmatter and 'name' in frontmatter:
                    skill = Skill(
                        name=frontmatter['name'],
                        path=skill_dir,
                        frontmatter=frontmatter
                    )
                    skills.append(skill)
            except Exception as e:
                console.print(f"[{COLORS['muted']}]{ICONS['warning']} Could not parse {skill_file}: {e}[/{COLORS['muted']}]")
        
        return sorted(skills, key=lambda s: s.name)
    
    def _extract_frontmatter(self, content: str) -> Optional[dict]:
        """Extract YAML frontmatter from skill content."""
        if not content.startswith('---'):
            return None
        
        # Find the end of frontmatter
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None
        
        try:
            frontmatter = yaml.safe_load(parts[1])
            return frontmatter
        except yaml.YAMLError:
            return None
    
    def import_skill(self, skill: Skill) -> bool:
        """Import a skill to the project directory."""
        # Ensure project skills directory exists
        self.project_skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Destination path
        dest_path = self.project_skills_dir / skill.name
        
        # Check if skill already exists
        if dest_path.exists():
            console.print(f"[{COLORS['warning']}]{ICONS['warning']} Skill '{skill.name}' already exists in project[/{COLORS['warning']}]")
            overwrite = questionary.confirm(
                "Overwrite?",
                default=False,
                style=custom_style
            ).ask()
            
            if not overwrite:
                console.print(f"[{COLORS['muted']}]{ICONS['info']} Import cancelled[/{COLORS['muted']}]")
                return False
            
            # Remove existing
            shutil.rmtree(dest_path)
        
        # Copy skill directory
        try:
            shutil.copytree(skill.path, dest_path)
            console.print(f"[{COLORS['success']}]{ICONS['success']} Successfully imported '{skill.name}' to project {ICONS['rocket']}[/{COLORS['success']}]")
            # Update imported skills set
            self.imported_skills.add(skill.name)
            return True
        except Exception as e:
            console.print(f"[{COLORS['accent']}]{ICONS['error']} Failed to import skill: {e}[/{COLORS['accent']}]")
            return False
    
    def show_skill_preview(self, skill: Skill):
        """Display a preview panel for the selected skill."""
        is_imported = skill.name in self.imported_skills
        preview = Panel(
            skill.get_preview(is_imported=is_imported),
            title=f"[bold {COLORS['primary']}]{ICONS['sparkle']} Skill Preview {ICONS['sparkle']}[/bold {COLORS['primary']}]",
            border_style=COLORS['primary'],
            padding=(1, 2)
        )
        console.print(preview)
    
    def run(self):
        """Run the interactive browser."""
        console.clear()
        
        # Styled banner/header
        banner = f"""
[bold {COLORS['header']}]╔════════════════════════════════════════════════════════════╗
║                                                            ║
║     {ICONS['skill']}  CLAUDE SKILLS BROWSER {ICONS['sparkle']}                     ║
║                                                            ║
║     Browse and import global skills to your project       ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝[/bold {COLORS['header']}]
        """
        console.print(banner)
        console.print()
        
        # Discover skills
        with console.status(f"[{COLORS['primary']}]{ICONS['search']} Discovering skills...[/{COLORS['primary']}]") as status:
            self.skills = self.discover_skills()
            if self.skills:
                self.update_imported_skills()
        
        if not self.skills:
            console.print(f"[{COLORS['warning']}]{ICONS['warning']} No skills found in global directory.[/{COLORS['warning']}]")
            console.print(f"[{COLORS['muted']}]{ICONS['info']} Add skills to: {self.global_skills_dir}[/{COLORS['muted']}]")
            console.print()
            console.print(f"[{COLORS['info']}]\nTip: Use 'python skill_generator.py' to create new skills![/{COLORS['info']}]")
            return
        
        # Display statistics
        imported_count = len(self.imported_skills)
        total_count = len(self.skills)
        new_count = total_count - imported_count
        
        stats_panel = Panel(
            f"[{COLORS['success']}]{ICONS['skill']} Total Skills: {total_count}[/{COLORS['success']}]  "
            f"[{COLORS['info']}]{ICONS['already_imported']} Already Imported: {imported_count}[/{COLORS['info']}]  "
            f"[{COLORS['warning']}]{ICONS['sparkle']} New Skills: {new_count}[/{COLORS['warning']}]",
            title=f"[bold {COLORS['primary']}]Statistics[/bold {COLORS['primary']}]",
            border_style=COLORS['muted'],
            padding=(0, 2)
        )
        console.print(stats_panel)
        console.print()
        
        # Keyboard shortcuts help
        help_text = (
            f"[{COLORS['primary']}]Navigation:[/{COLORS['primary']}] ↑/↓ arrows  "
            f"[{COLORS['primary']}]|[/{COLORS['primary']}]  "
            f"[{COLORS['success']}]Select:[/{COLORS['success']}] Enter  "
            f"[{COLORS['primary']}]|[/{COLORS['primary']}]  "
            f"[{COLORS['accent']}]Exit:[/{COLORS['accent']}] Select '[Exit Browser]'"
        )
        console.print(Panel(help_text, border_style=COLORS['muted'], padding=(0, 1)))
        console.print()
        
        # Main loop - keep running until user quits
        while True:
            try:
                # Create choices for questionary
                choices = []
                for skill in self.skills:
                    is_imported = skill.name in self.imported_skills
                    choices.append(questionary.Choice(
                        title=skill.get_display_name(is_imported=is_imported),
                        value=skill
                    ))
                
                # Add exit option (using a unique sentinel value instead of None)
                EXIT_SENTINEL = "__EXIT__"
                choices.append(questionary.Choice(
                    title=f"[{ICONS['wave']} Exit Browser]",
                    value=EXIT_SENTINEL
                ))
                
                # Show interactive selection
                selected = questionary.select(
                    f"Select a skill to import:",
                    choices=choices,
                    style=custom_style,
                    use_shortcuts=False,
                    use_arrow_keys=True,
                    instruction=""
                ).ask()
                
                # Handle selection
                if selected == "__EXIT__" or selected is None:
                    # User chose exit
                    console.print(f"\n[{COLORS['primary']}]Goodbye! {ICONS['wave']}[/{COLORS['primary']}]")
                    break
                
                # Safety check: ensure we have a Skill object
                if not isinstance(selected, Skill):
                    console.print(f"[{COLORS['accent']}]{ICONS['error']} Error: Invalid selection (got {type(selected).__name__} instead of Skill)[/{COLORS['accent']}]")
                    continue
                
                console.print()
                
                # Show preview
                self.show_skill_preview(selected)
                console.print()
                
                # Check if already imported
                if selected.name in self.imported_skills:
                    console.print(f"[{COLORS['info']}]{ICONS['info']} This skill is already imported in your project.[/{COLORS['info']}]")
                    console.print()
                
                # Confirm import
                confirm = questionary.confirm(
                    f"Import '{selected.name}' to project?",
                    default=True,
                    style=custom_style
                ).ask()
                
                if confirm:
                    self.import_skill(selected)
                    console.print()
                
                # Ask if user wants to continue
                console.print()
                continue_browsing = questionary.confirm(
                    "Import another skill?",
                    default=True,
                    style=custom_style
                ).ask()
                
                if not continue_browsing:
                    console.print(f"\n[{COLORS['primary']}]Goodbye! {ICONS['wave']}[/{COLORS['primary']}]")
                    break
                
                console.print()
                
            except KeyboardInterrupt:
                console.print(f"\n\n[{COLORS['warning']}]Cancelled by user[/{COLORS['warning']}]")
                break
            except Exception as e:
                console.print(f"\n[{COLORS['accent']}]{ICONS['error']} Error: {e}[/{COLORS['accent']}]")
                if '--debug' in sys.argv:
                    raise
                break


def main():
    """Main entry point."""
    try:
        browser = SkillsBrowser()
        browser.run()
    except KeyboardInterrupt:
        console.print(f"\n[{COLORS['warning']}]Cancelled by user[/{COLORS['warning']}]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[{COLORS['accent']}]{ICONS['error']} Error: {e}[/{COLORS['accent']}]")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
