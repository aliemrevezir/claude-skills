#!/usr/bin/env python3
"""
Claude Skills Manager - Main CLI Application

This is the main entry point for managing Claude Skills. It provides access to:
- Skill Generator: Create new skills interactively with AI assistance
- Skills Browser: Browse and import global skills to your project

Usage:
    python claude_skills.py           # Show interactive menu
    python claude_skills.py generate  # Launch skill generator
    python claude_skills.py browse    # Launch skills browser
    python claude_skills.py projects  # Import skills into another project
"""

import sys
import subprocess
import platform
from pathlib import Path
import click
import yaml
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

console = Console()
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def get_cancel_key_info():
    """Get OS-specific keyboard shortcut for canceling"""
    system = platform.system()
    if system == "Darwin":  # macOS
        return "Ctrl+C", "macOS"
    elif system == "Windows":
        return "Ctrl+C", "Windows"
    else:  # Linux and others
        return "Ctrl+C", "Linux"


def display_welcome():
    """Display welcome message and main menu"""
    console.clear()
    
    # Create welcome panel
    welcome_text = Text.from_markup(
        "[bold cyan]Welcome to Claude Skills Manager[/bold cyan]\n\n"
        "This tool helps you create and manage Claude Skills for your projects.\n"
        "Choose an option below to get started."
    )
    
    console.print(Panel(
        welcome_text,
        title="[bold]🚀 Claude Skills Manager[/bold]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()


def display_menu():
    """Display the main menu options"""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Option", style="bold magenta", width=8)
    table.add_column("Description", style="white")
    
    table.add_row(
        "[1]",
        "[bold cyan]Generate New Skill[/bold cyan]\n"
        "Create a new Claude skill interactively using AI assistance.\n"
        "The AI will ask you questions to understand your needs and\n"
        "generate a properly formatted SKILL.md file."
    )
    table.add_row("", "")  # Spacer
    table.add_row(
        "[2]",
        "[bold cyan]Browse Global Skills[/bold cyan]\n"
        "Browse and import existing skills from the global skills library.\n"
        "Use arrow keys to navigate and Enter to import a skill to your project."
    )
    table.add_row("", "")  # Spacer
    table.add_row(
        "[3]",
        "[bold cyan]Project Imports & Settings[/bold cyan]\n"
        "Manage root directories and target folders, then import skills\n"
        "into another project's skills directory."
    )
    table.add_row("", "")  # Spacer
    table.add_row(
        "[4]",
        "[bold cyan]LLM Provider Settings[/bold cyan]\n"
        "Choose which configured LLM provider to use (openai / anthropic / gemini)"
    )
    table.add_row("", "")  # Spacer
    table.add_row(
        "[5]",
        "[bold cyan]Help & Documentation[/bold cyan]\n"
        "View detailed information about using this tool and managing skills."
    )
    table.add_row("", "")  # Spacer
    table.add_row(
        "[Q]",
        "[dim]Exit[/dim]"
    )
    
    console.print(table)
    console.print()
    
    # Add helpful footer
    cancel_key, os_name = get_cancel_key_info()
    footer_text = Text.from_markup(
        f"[dim]💡 Tip: When using a tool, press [bold]{cancel_key}[/bold] anytime to return to this menu[/dim]"
    )
    console.print(footer_text)
    console.print()


def display_help():
    """Display help and documentation"""
    console.clear()
    
    help_text = """[bold cyan]Claude Skills Manager - Help[/bold cyan]

[bold]What are Claude Skills?[/bold]
Claude Skills are custom instructions that extend Claude's capabilities for specific tasks.
They are stored as SKILL.md files and automatically discovered by Claude when relevant.

[bold]Skill Generator[/bold]
Creates new skills interactively:
  • The AI asks intelligent questions to understand your needs
  • Generates properly formatted SKILL.md files
  • Validates the output for correctness
  • Supports both personal and project-specific skills

[bold]Skills Browser[/bold]
Browses and imports existing skills:
  • View all available global skills
  • Navigate with arrow keys (↑/↓)
  • Preview skill details
  • Import to your project with Enter
  • Continue browsing after import

[bold]File Locations[/bold]
  • Personal skills: ~/.claude/skills/
  • Project skills: .claude/skills/
  • Configuration: config.yaml

[bold]Command Line Usage[/bold]
  python claude_skills.py           # Interactive menu
  python claude_skills.py generate  # Direct to skill generator
  python claude_skills.py browse    # Direct to skills browser
  python claude_skills.py llm       # Choose LLM provider
  python claude_skills.py projects  # Import skills into another project

[bold]Environment Setup[/bold]
Make sure you have:
  • Python 3.8 or later
  • Required packages (pip install -r requirements.txt)
  • GEMINI_API_KEY in your .env file (for skill generation)

[bold]For More Information[/bold]
  • README.md - Complete documentation
  • QUICKSTART.md - Quick start guide
  • Examples in examples/ directory
"""
    
    console.print(Panel(help_text, title="[bold]📚 Help & Documentation[/bold]", border_style="cyan"))
    console.print()
    input("Press Enter to return to main menu...")


def run_skill_generator():
    """Launch the skill generator"""
    console.clear()
    console.print("[bold cyan]Launching Skill Generator...[/bold cyan]")
    
    # Show how to return to menu
    cancel_key, os_name = get_cancel_key_info()
    console.print(f"[dim]Press [bold]{cancel_key}[/bold] at any time to return to main menu[/dim]")
    console.print()
    
    script_path = Path(__file__).parent / "skill_generator.py"
    
    if not script_path.exists():
        console.print("[bold red]Error:[/bold red] skill_generator.py not found!")
        console.print(f"Expected location: {script_path}")
        return False
    
    try:
        # Run the skill generator script
        result = subprocess.run([sys.executable, str(script_path)], check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        console.print("\n[yellow]Returned to main menu.[/yellow]")
        return False
    except Exception as e:
        console.print(f"[bold red]Error launching skill generator:[/bold red] {e}")
        return False


def run_skills_browser():
    """Launch the skills browser"""
    console.clear()
    console.print("[bold cyan]Launching Skills Browser...[/bold cyan]")
    
    # Show how to return to menu
    cancel_key, os_name = get_cancel_key_info()
    console.print(f"[dim]Press [bold]{cancel_key}[/bold] at any time to return to main menu[/dim]")
    console.print()
    
    script_path = Path(__file__).parent / "skills_browser.py"
    
    if not script_path.exists():
        console.print("[bold red]Error:[/bold red] skills_browser.py not found!")
        console.print(f"Expected location: {script_path}")
        return False
    
    try:
        # Run the skills browser script
        result = subprocess.run([sys.executable, str(script_path)], check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        console.print("\n[yellow]Returned to main menu.[/yellow]")
        return False
    except Exception as e:
        console.print(f"[bold red]Error launching skills browser:[/bold red] {e}")
        return False


def run_project_importer():
    """Launch the project skill importer"""
    console.clear()
    console.print("[bold cyan]Launching Project Skill Importer...[/bold cyan]")
    console.print()

    script_path = Path(__file__).parent / "project_importer.py"
    if not script_path.exists():
        console.print("[bold red]Error:[/bold red] project_importer.py not found!")
        console.print(f"Expected location: {script_path}")
        return False

    try:
        result = subprocess.run([sys.executable, str(script_path)], check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        console.print("\n[yellow]Returned to main menu.[/yellow]")
        return False
    except Exception as e:
        console.print(f"[bold red]Error launching project importer:[/bold red] {e}")
        return False


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _save_yaml(path: Path, data: dict):
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, default_flow_style=False, indent=2)


def run_llm_settings():
    """Allow user to pick which configured LLM provider to use."""
    console.clear()
    console.print("[bold cyan]LLM Provider Settings[/bold cyan]\n")

    cfg = _load_yaml(CONFIG_PATH)
    providers_cfg = cfg.get("providers", {}) if isinstance(cfg, dict) else {}
    available = [p for p in providers_cfg.keys() if isinstance(p, str)]
    if not available:
        console.print("[red]No providers found in config.yaml -> providers.[/red]")
        console.print("Add at least one (openai / anthropic / gemini) then retry.")
        return False

    current = (cfg.get("llm", {}) or {}).get("provider", "openai")
    choice = questionary.select(
        "Select LLM provider",
        choices=[questionary.Choice(title=p, value=p, checked=(p == current)) for p in available],
        default=current if current in available else None,
    ).ask()

    if not choice:
        console.print("[yellow]No change made.[/yellow]")
        return False

    # Persist selection
    if "llm" not in cfg or not isinstance(cfg.get("llm"), dict):
        cfg["llm"] = {}
    cfg["llm"]["provider"] = choice
    _save_yaml(CONFIG_PATH, cfg)

    console.print(f"[green]Provider set to:[/green] {choice}")
    return True


def interactive_menu():
    """Run the interactive menu loop"""
    while True:
        display_welcome()
        display_menu()
        
        choice = console.input("[bold cyan]Select an option[/bold cyan] [1-5, Q]: ").strip().lower()
        
        if choice == '1':
            run_skill_generator()
            console.print()
            input("Press Enter to return to main menu...")
        elif choice == '2':
            run_skills_browser()
            console.print()
            input("Press Enter to return to main menu...")
        elif choice == '3':
            run_project_importer()
            console.print()
            input("Press Enter to return to main menu...")
        elif choice == '4':
            run_llm_settings()
            console.print()
            input("Press Enter to return to main menu...")
        elif choice == '5':
            display_help()
        elif choice == 'q':
            console.print("\n[bold cyan]Thank you for using Claude Skills Manager![/bold cyan]")
            console.print("[dim]Happy skill building! 🚀[/dim]\n")
            break
        else:
            console.print("\n[yellow]Invalid option. Please choose 1, 2, 3, 4, 5, or Q.[/yellow]")
            console.print()
            input("Press Enter to continue...")


@click.command()
@click.argument('command', required=False, type=click.Choice(['generate', 'browse', 'projects', 'llm'], case_sensitive=False))
def main(command):
    """
    Claude Skills Manager - Create and manage Claude Skills
    
    Run without arguments for an interactive menu, or use:
    
    \b
    Commands:
        generate    Launch the skill generator
        browse      Launch the skills browser
        projects    Import skills into another project
        llm         Choose LLM provider from config.yaml
    
    \b
    Examples:
        python claude_skills.py              # Interactive menu
        python claude_skills.py generate     # Direct to skill generator
        python claude_skills.py browse       # Direct to skills browser
        python claude_skills.py projects     # Import skills into another project
        python claude_skills.py llm          # Pick LLM provider
    """
    try:
        if command == 'generate':
            run_skill_generator()
        elif command == 'browse':
            run_skills_browser()
        elif command == 'projects':
            run_project_importer()
        elif command == 'llm':
            run_llm_settings()
        else:
            # No command specified, show interactive menu
            interactive_menu()
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
