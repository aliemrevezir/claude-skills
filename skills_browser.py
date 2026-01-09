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

# Custom style for the interactive browser
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
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
    
    def get_display_name(self):
        """Get formatted display name for the list."""
        return f"{self.name}"
    
    def get_preview(self) -> str:
        """Get detailed preview of the skill."""
        lines = [
            f"[bold cyan]{self.name}[/bold cyan]",
            "",
            f"[dim]Description:[/dim]",
            self.description,
            "",
        ]
        
        if self.allowed_tools:
            lines.extend([
                f"[dim]Allowed Tools:[/dim]",
                str(self.allowed_tools),
                ""
            ])
        
        lines.extend([
            f"[dim]User Invocable:[/dim] {'Yes' if self.user_invocable else 'No'}",
            f"[dim]Location:[/dim] {self.path}",
        ])
        
        return "\n".join(lines)


class SkillsBrowser:
    """Browser for discovering and importing Claude skills."""
    
    def __init__(self):
        self.global_skills_dir = Path.home() / ".claude" / "skills"
        self.project_skills_dir = Path(".claude") / "skills"
        self.skills: List[Skill] = []
    
    def discover_skills(self) -> List[Skill]:
        """Discover all skills in the global directory."""
        skills = []
        
        if not self.global_skills_dir.exists():
            console.print(f"[yellow]Global skills directory not found: {self.global_skills_dir}[/yellow]")
            console.print("[yellow]Creating directory...[/yellow]")
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
                console.print(f"[dim]Warning: Could not parse {skill_file}: {e}[/dim]")
        
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
            console.print(f"[yellow]⚠ Skill '{skill.name}' already exists in project[/yellow]")
            overwrite = questionary.confirm(
                "Overwrite?",
                default=False,
                style=custom_style
            ).ask()
            
            if not overwrite:
                console.print("[dim]Import cancelled[/dim]")
                return False
            
            # Remove existing
            shutil.rmtree(dest_path)
        
        # Copy skill directory
        try:
            shutil.copytree(skill.path, dest_path)
            console.print(f"[green]✓ Successfully imported '{skill.name}' to project[/green]")
            return True
        except Exception as e:
            console.print(f"[red]✗ Failed to import skill: {e}[/red]")
            return False
    
    def show_skill_preview(self, skill: Skill):
        """Display a preview panel for the selected skill."""
        preview = Panel(
            skill.get_preview(),
            title="[bold]Skill Preview[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(preview)
    
    def run(self):
        """Run the interactive browser."""
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]Claude Skills Browser[/bold cyan]\n"
            "Browse and import global skills to your project",
            border_style="cyan"
        ))
        console.print()
        
        # Discover skills
        with console.status("[cyan]Discovering skills...[/cyan]"):
            self.skills = self.discover_skills()
        
        if not self.skills:
            console.print("[yellow]No skills found in global directory.[/yellow]")
            console.print(f"[dim]Add skills to: {self.global_skills_dir}[/dim]")
            return
        
        console.print(f"[green]Found {len(self.skills)} skill(s)[/green]")
        console.print()
        
        # Main loop - keep running until user quits
        while True:
            try:
                # Create choices for questionary
                choices = [
                    questionary.Choice(
                        title=skill.get_display_name(),
                        value=skill
                    )
                    for skill in self.skills
                ]
                
                # Add separator and exit option
                choices.append(questionary.Separator())
                choices.append(questionary.Choice(
                    title="[Exit Browser]",
                    value=None
                ))
                
                # Show interactive selection
                console.print("[dim]Use ↑/↓ arrows to navigate, Enter to import, or select Exit[/dim]")
                selected = questionary.select(
                    "Select a skill to import:",
                    choices=choices,
                    style=custom_style,
                    use_shortcuts=False,
                    use_arrow_keys=True,
                    instruction=""
                ).ask()
                
                # Handle selection
                if selected is None:
                    # User chose exit
                    console.print("\n[cyan]Goodbye! 👋[/cyan]")
                    break
                
                console.print()
                
                # Show preview
                self.show_skill_preview(selected)
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
                    console.print("\n[cyan]Goodbye! 👋[/cyan]")
                    break
                
                console.print()
                
            except KeyboardInterrupt:
                console.print("\n\n[yellow]Cancelled by user[/yellow]")
                break
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]")
                if '--debug' in sys.argv:
                    raise
                break


def main():
    """Main entry point."""
    try:
        browser = SkillsBrowser()
        browser.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
