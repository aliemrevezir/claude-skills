#!/usr/bin/env python3
"""
Claude Skills Generator - Interactive skill creation tool using Gemini AI.

This tool helps you create high-quality Claude Skills by asking intelligent
questions and generating properly formatted SKILL.md files.
"""

import os
import sys
from pathlib import Path
import yaml
import click
from rich.console import Console

from gemini_client import GeminiClient
from question_engine import QuestionEngine
from skill_validator import SkillValidator
from preferences import PreferencesManager


console = Console()


def get_output_path(location: str, skill_name: str, config: dict) -> Path:
    """
    Determine the output path for the skill.
    
    Args:
        location: 'personal', 'project', or custom path
        skill_name: Name of the skill
        config: Configuration dictionary
        
    Returns:
        Path object for the skill directory
    """
    if location == 'personal':
        base_path = Path(config['output']['personal_path']).expanduser()
    elif location == 'project':
        base_path = Path(config['output']['project_path'])
    else:
        base_path = Path(location)
    
    skill_dir = base_path / skill_name
    return skill_dir


@click.command()
@click.argument('intent', required=False)
@click.option(
    '--output', '-o',
    type=str,
    default=None,
    help='Output location: "personal", "project", or custom path'
)
@click.option(
    '--config', '-c',
    type=click.Path(exists=True),
    default='config.yaml',
    help='Path to configuration file'
)
def main(intent: str, output: str, config: str):
    """
    Claude Skills Generator - Create skills interactively with Gemini AI.
    
    INTENT: Optional initial description of what you want the skill to do.
            If not provided, you'll be prompted interactively.
    
    Examples:
        skill_generator.py
        skill_generator.py "Create a skill for reviewing pull requests"
        skill_generator.py --output personal
        skill_generator.py --output ~/.claude/skills/custom
    """
    try:
        # Load configuration
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Initialize preferences manager
        prefs = PreferencesManager()
        
        # Initialize components
        gemini = GeminiClient(config)
        question_engine = QuestionEngine(
            max_questions=config_data['questions']['max_questions']
        )
        validator = SkillValidator(config_data)
        
        # Display welcome
        question_engine.display_welcome()
        
        # Ask for output location first (doesn't count toward question limit)
        if output is None:
            output = question_engine.get_output_location(prefs)
        
        # Ask about hooks preference (doesn't count toward question limit)
        wants_hooks = question_engine.get_hooks_preference()
        
        # Get initial intent
        if not intent:
            intent = question_engine.get_initial_intent()
        else:
            console.print(f"[cyan]Creating skill for:[/cyan] {intent}")
            console.print()
        
        # Start conversation with Gemini
        questions = gemini.start_conversation(intent, wants_hooks)
        
        # Interactive Q&A loop
        while questions and question_engine.questions_asked < question_engine.max_questions:
            # Ask questions and get answers
            answers = question_engine.ask_questions(questions)
            
            # Get follow-up questions if needed
            questions = gemini.ask_followup_questions(
                question_engine.answers,
                question_engine.questions_asked
            )
        
        # Confirm before generation
        if not question_engine.confirm_generation():
            console.print("[yellow]Generation cancelled.[/yellow]")
            return
        
        # Generate skill
        question_engine.display_generating()
        skill_content = gemini.generate_skill()
        
        # Validate generated content
        is_valid, errors = validator.validate(skill_content)
        
        if not is_valid:
            question_engine.display_error(errors, skill_content, gemini.debug_log_file)
            console.print("[yellow]Would you like to save it anyway?[/yellow]")
            if not click.confirm("Save despite validation errors?"):
                console.print(f"\n[dim]Debug information saved to: {gemini.debug_log_file}[/dim]")
                return
        
        # Get skill name from generated content
        frontmatter = validator.get_frontmatter(skill_content)
        if not frontmatter or 'name' not in frontmatter:
            console.print("[red]Error: Could not extract skill name from generated content[/red]")
            console.print(f"\n[dim]Debug information saved to: {gemini.debug_log_file or gemini._temp_log_file}[/dim]")
            return
        
        skill_name = frontmatter['name']
        
        # Finalize log file with skill name
        gemini.finalize_log(skill_name)
        
        # Determine output location
        if output is None:
            output = config_data['output']['default_location']
        
        output_path = get_output_path(output, skill_name, config_data)
        
        # Create directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Write SKILL.md file
        skill_file = output_path / 'SKILL.md'
        skill_file.write_text(skill_content)
        
        # Display success
        question_engine.display_skill_preview(skill_content)
        question_engine.display_success(str(skill_file))
        
        # Offer to create supporting files
        if click.confirm("\nWould you like to create supporting files (README, examples)?"):
            create_supporting_files(output_path, skill_name, frontmatter)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Generation cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


def create_supporting_files(skill_dir: Path, skill_name: str, frontmatter: dict):
    """Create optional supporting files for the skill."""
    # Create README.md
    readme_content = f"""# {skill_name}

{frontmatter.get('description', 'No description provided')}

## Usage

This skill is automatically discovered by Claude when relevant to your conversation.

To test it, ask Claude to perform tasks related to: {frontmatter.get('description', '')}

## Files

- `SKILL.md` - Main skill file with instructions

## Configuration

- **Name**: {skill_name}
- **Description**: {frontmatter.get('description', '')}
"""
    
    if 'allowed-tools' in frontmatter:
        readme_content += f"\n- **Allowed Tools**: {frontmatter['allowed-tools']}"
    
    readme_file = skill_dir / 'README.md'
    readme_file.write_text(readme_content)
    console.print(f"[green]✓[/green] Created {readme_file}")
    
    # Create examples directory
    examples_dir = skill_dir / 'examples'
    examples_dir.mkdir(exist_ok=True)
    
    example_content = f"""# Examples for {skill_name}

Add example usage scenarios here to help users understand how to use this skill.

## Example 1

[Describe a scenario]

## Example 2

[Describe another scenario]
"""
    
    examples_file = examples_dir / 'examples.md'
    examples_file.write_text(example_content)
    console.print(f"[green]✓[/green] Created {examples_file}")


if __name__ == '__main__':
    main()
