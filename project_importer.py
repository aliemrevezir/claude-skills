#!/usr/bin/env python3
"""
Project Skill Importer

Lets users:
- Register one or more GitHub/work roots (saved to config.yaml)
- Browse projects under those roots
- Import an existing SKILL.md directory into a selected project's .claude/skills/
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import yaml

console = Console()

# Runtime config state
CURRENT_CONFIG: Dict[str, Any] = {}
CURRENT_TARGETS: List[str] = [".claude/skills"]
TARGET_OPTIONS: List[str] = [".claude/skills", ".codex/skills", ".agent/skills", ".agents/skills"]

COLORS = {
    "primary": "#4ECDC4",
    "accent": "#FF6B6B",
    "success": "#51CF66",
    "warning": "#FFD93D",
    "muted": "#858585",
    "header": "#FF6B6B",
    "highlight": "#4ECDC4",
}

custom_style = Style(
    [
        ("qmark", f"fg:{COLORS['primary']} bold"),
        ("question", "bold"),
        ("answer", f"fg:{COLORS['accent']} bold"),
        ("pointer", f"fg:{COLORS['primary']} bold"),
        ("highlighted", f"fg:{COLORS['highlight']} bold"),
        ("selected", f"fg:{COLORS['success']} bold"),
        ("separator", f"fg:{COLORS['muted']}"),
        ("disabled", "fg:#858585 italic"),
    ]
)


@dataclass(frozen=True)
class SkillDir:
    name: str
    path: Path
    description: str = ""

    def display(self) -> str:
        desc = (self.description or "").strip()
        if desc:
            short = desc.replace("\n", " ")
            if len(short) > 80:
                short = short[:77] + "..."
            return f"{self.name} — {short}"
        return self.name


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid config (expected YAML mapping): {path}")
    return data


def _dump_projects_block(roots: List[str]) -> str:
    block = {
        "projects": {
            "roots": roots,
        }
    }
    text = yaml.safe_dump(
        block,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        indent=2,
    )
    # Ensure it ends with exactly one newline.
    return text.rstrip() + "\n"


def _upsert_projects_section(config_path: Path, roots: List[str]) -> None:
    raw = config_path.read_text()
    new_block = _dump_projects_block(roots)

    lines = raw.splitlines(keepends=True)
    start: Optional[int] = None
    for idx, line in enumerate(lines):
        if re.match(r"^projects:\s*$", line):
            start = idx
            break

    if start is None:
        # Append section at end to preserve existing comments/formatting.
        suffix = "\n# Project import settings\n" + new_block
        config_path.write_text(raw.rstrip() + suffix)
        return

    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.startswith((" ", "\t")):
            end += 1
            continue
        if line.strip() == "":
            end += 1
            continue
        if line.startswith("#"):
            # Stop before top-level comment belonging to next section.
            break
        if re.match(r"^[A-Za-z0-9_-]+:\s*", line):
            break
        end += 1

    before = "".join(lines[:start])
    after = "".join(lines[end:])
    config_path.write_text(before + new_block + after)


def get_project_roots(config: Dict[str, Any]) -> List[str]:
    projects = config.get("projects", {})
    if not isinstance(projects, dict):
        return []
    roots = projects.get("roots", [])
    if not isinstance(roots, list):
        return []
    out: List[str] = []
    for item in roots:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    # De-dup while preserving order
    seen = set()
    deduped: List[str] = []
    for r in out:
        if r in seen:
            continue
        seen.add(r)
        deduped.append(r)
    return deduped


def _expand_dir(p: str) -> Path:
    return Path(p).expanduser().resolve()


def _get_target_config(config: Dict[str, Any]) -> Tuple[str, List[str]]:
    targets = config.get("skill_targets", {}) if isinstance(config, dict) else {}
    default = targets.get("default") if isinstance(targets, dict) else None
    options = targets.get("options") if isinstance(targets, dict) else None
    selected = targets.get("selected") if isinstance(targets, dict) else None
    opt_list: List[str] = []
    if isinstance(options, list):
        for o in options:
            if isinstance(o, str) and o.strip():
                opt_list.append(o.strip())
    if not default:
        default = ".claude/skills"
    if default not in opt_list:
        opt_list.insert(0, default)
    sel_list: List[str] = []
    if isinstance(selected, list):
        for s in selected:
            if isinstance(s, str) and s.strip():
                sel_list.append(s.strip())
    if not sel_list:
        sel_list = [default]
    # Ensure selected are part of options
    for s in sel_list:
        if s not in opt_list:
            opt_list.append(s)
    return default, opt_list, sel_list


def _set_target_config(config_path: Path, default_target: str, options: List[str], selected: List[str]) -> None:
    raw = _load_yaml(config_path)
    if "skill_targets" not in raw or not isinstance(raw.get("skill_targets"), dict):
        raw["skill_targets"] = {}
    raw["skill_targets"]["default"] = default_target
    raw["skill_targets"]["options"] = options
    raw["skill_targets"]["selected"] = selected
    config_path.write_text(
        yaml.safe_dump(
            raw,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            indent=2,
        )
    )


def _get_target_subdirs() -> List[str]:
    return CURRENT_TARGETS


def _validate_dir_input(value: str) -> bool | str:
    if not value or not value.strip():
        return "Please enter a directory path."
    path = _expand_dir(value.strip())
    if not path.exists():
        return f"Directory does not exist: {path}"
    if not path.is_dir():
        return f"Not a directory: {path}"
    return True


def _discover_projects(root: Path) -> List[Path]:
    if not root.exists() or not root.is_dir():
        return []
    projects: List[Path] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        projects.append(child)
    return projects


def _extract_frontmatter(content: str) -> Optional[dict]:
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1])
    except Exception:
        return None


def _discover_skills(skills_dir: Path) -> List[SkillDir]:
    if not skills_dir.exists() or not skills_dir.is_dir():
        return []
    skills: List[SkillDir] = []
    for entry in sorted(skills_dir.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir():
            continue
        skill_file = entry / "SKILL.md"
        if not skill_file.exists():
            continue
        name = entry.name
        description = ""
        try:
            fm = _extract_frontmatter(skill_file.read_text()) or {}
            if isinstance(fm, dict):
                if isinstance(fm.get("name"), str) and fm["name"].strip():
                    name = fm["name"].strip()
                desc_val = fm.get("description")
                if isinstance(desc_val, str):
                    description = desc_val
        except Exception:
            pass
        skills.append(SkillDir(name=name, path=entry, description=description))
    return skills


def _pick_skill_source() -> Optional[Path]:
    options: List[Tuple[str, Path]] = []
    options.append(("Personal skills (~/.claude/skills)", Path.home() / ".claude" / "skills"))
    options.append(("This project's skills (.claude/skills)", Path(".claude") / "skills"))

    choice = questionary.select(
        "Select skill source",
        choices=[o[0] for o in options] + ["Custom path...", "Back"],
        style=custom_style,
    ).ask()
    if not choice or choice == "Back":
        return None
    if choice == "Custom path...":
        custom = questionary.path(
            "Enter skills directory (contains skill folders with SKILL.md)",
            validate=_validate_dir_input,
            style=custom_style,
        ).ask()
        if not custom:
            return None
        return _expand_dir(custom)
    for label, path in options:
        if choice == label:
            return path
    return None


def _import_skill_to_project(skill: SkillDir, project_dir: Path) -> bool:
    targets = _get_target_subdirs()
    if not targets:
        console.print(f"[{COLORS['warning']}]No target folders configured.[/{COLORS['warning']}]")
        return False

    for target in targets:
        dest_root = project_dir / target
        dest_root.mkdir(parents=True, exist_ok=True)
        dest_path = dest_root / skill.name

        if dest_path.exists():
            overwrite = questionary.confirm(
                f"'{skill.name}' already exists in {dest_root}. Overwrite?",
                default=False,
                style=custom_style,
            ).ask()
            if not overwrite:
                continue
            shutil.rmtree(dest_path)

        shutil.copytree(skill.path, dest_path)

    return True


def _render_home(config_path: Path, roots: List[str]) -> None:
    console.clear()
    title = "[bold cyan]Project Skill Importer[/bold cyan]"
    roots_text = "\n".join([f"- {r}" for r in roots]) if roots else "[dim]No roots configured yet.[/dim]"
    targets = _get_target_subdirs()
    targets_text = "\n".join([f"- {t}" for t in targets]) if targets else "[dim]No targets selected.[/dim]"
    panel = Panel(
        f"{title}\n\n[bold]{config_path}[/bold]\n\n"
        f"[bold {COLORS['primary']}]GitHub / work roots[/bold {COLORS['primary']}]\n{roots_text}\n\n"
        f"[bold {COLORS['primary']}]Target folders[/bold {COLORS['primary']}]\n{targets_text}",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
    console.print()


def _settings_menu(config_path: Path, roots: List[str]) -> List[str]:
    while True:
        _render_home(config_path, roots)
        action = questionary.select(
            "Settings",
            choices=[
                "Add root directory",
                "Remove root directory",
                "Change skill target folders",
                "Back",
            ],
            style=custom_style,
        ).ask()

        if not action or action == "Back":
            return roots

        if action == "Add root directory":
            hint = f"Enter a GitHub/work directory (projects are listed from its direct subfolders)\nHint: current dir: {Path.cwd()}"
            new_root = questionary.path(
                hint,
                validate=_validate_dir_input,
                style=custom_style,
            ).ask()
            if not new_root:
                continue
            normalized_path = _expand_dir(new_root)
            normalized = str(normalized_path)

            projects = _discover_projects(normalized_path)
            if not projects:
                console.print(f"[{COLORS['warning']}]No projects found under {normalized_path}.[/{COLORS['warning']}]")
                questionary.press_any_key_to_continue().ask()
                continue

            choices = []
            for p in projects:
                choices.append(
                    questionary.Choice(
                        title=f"☐ {p.name}",
                        value=p.name,
                        checked=True,
                    )
                )

            selected = questionary.checkbox(
                "Select repos to activate (space toggles, enter confirms):",
                choices=choices + ["[Skip]"],
                style=custom_style,
                instruction="Press space to toggle, enter to confirm",
            ).ask()
            if not selected or selected == "[Skip]":
                continue

            summary = "\n".join([f"[green]■[/green] {name}" for name in selected if name != "[Skip]"])
            console.print(Panel(summary or "[dim]No repos selected[/dim]", title="Repositories to add", border_style="green"))
            confirm = questionary.confirm(
                f"Add root {normalized_path} with {len([s for s in selected if s != '[Skip]'])} repos?",
                default=True,
                style=custom_style,
            ).ask()
            if not confirm:
                continue

            if normalized not in roots:
                roots.append(normalized)
                _upsert_projects_section(config_path, roots)
            continue

        if action == "Remove root directory":
            if not roots:
                console.print(f"[{COLORS['warning']}]No roots to remove.[/{COLORS['warning']}]")
                questionary.press_any_key_to_continue().ask()
                continue
            to_remove = questionary.checkbox(
                "Select roots to remove",
                choices=roots,
                style=custom_style,
            ).ask()
            if not to_remove:
                continue
            roots = [r for r in roots if r not in set(to_remove)]
            _upsert_projects_section(config_path, roots)
            continue

        if action == "Change skill target folders":
            default, options, selected = _get_target_config(CURRENT_CONFIG)

            choices = [questionary.Choice(title=opt, value=opt, checked=opt in selected) for opt in options]
            choices.append(questionary.Choice(title="Custom...", value="__custom__"))
            choices.append(questionary.Choice(title="Back", value="__back__"))

            result = questionary.checkbox(
                "Select one or more target folders (relative to project root)",
                choices=choices,
                style=custom_style,
                instruction="Space to toggle, enter to confirm",
            ).ask()
            if not result or "__back__" in result:
                continue

            new_selected = [r for r in result if r not in {"__custom__", "__back__"}]

            if "__custom__" in result:
                custom = questionary.text(
                    "Enter relative path (e.g. .codex/skills or skills):",
                    validate=lambda v: bool(v.strip()),
                    style=custom_style,
                ).ask()
                if custom and custom.strip():
                    new_selected.append(custom.strip())
                    if custom.strip() not in options:
                        options.insert(0, custom.strip())

            if not new_selected:
                console.print(f"[{COLORS['warning']}]No targets selected; keeping previous selection.[/{COLORS['warning']}]")
                continue

            global CURRENT_TARGETS
            CURRENT_TARGETS = new_selected

            # Default = first selected
            new_default = new_selected[0]
            _set_target_config(config_path, new_default, options, new_selected)

            # Refresh CURRENT_CONFIG from disk
            try:
                CURRENT_CONFIG.update(_load_yaml(config_path))
            except Exception:
                pass
            continue


def _select_project(roots: List[str]) -> Optional[Path]:
    if not roots:
        return None

    root_choice = questionary.select(
        "Select a root",
        choices=[str(r) for r in roots] + ["Back"],
        style=custom_style,
    ).ask()
    if not root_choice or root_choice == "Back":
        return None

    root_path = _expand_dir(root_choice)
    projects = _discover_projects(root_path)
    if not projects:
        console.print(f"[{COLORS['warning']}]No projects found under: {root_path}[/{COLORS['warning']}]")
        questionary.press_any_key_to_continue().ask()
        return None

    project_choice = questionary.select(
        "Select a project (arrow keys, Enter to confirm)",
        choices=[p.name for p in projects] + ["Back"],
        style=custom_style,
    ).ask()
    if not project_choice or project_choice == "Back":
        return None
    for p in projects:
        if p.name == project_choice:
            return p
    return None


def _import_flow(roots: List[str]) -> None:
    project_dir = _select_project(roots)
    if project_dir is None:
        return

    source_dir = _pick_skill_source()
    if source_dir is None:
        return

    skills = _discover_skills(source_dir)
    if not skills:
        console.print(f"[{COLORS['warning']}]No skills found in: {source_dir}[/{COLORS['warning']}]")
        questionary.press_any_key_to_continue().ask()
        return

    choice = questionary.select(
        "Select a skill to import (arrow keys, Enter to confirm)",
        choices=[s.display() for s in skills] + ["Back"],
        style=custom_style,
    ).ask()
    if not choice or choice == "Back":
        return

    selected: Optional[SkillDir] = None
    for s in skills:
        if s.display() == choice:
            selected = s
            break
    if selected is None:
        return

    try:
        targets_used = _get_target_subdirs()
        ok = _import_skill_to_project(selected, project_dir)
    except Exception as e:
        console.print(f"[{COLORS['accent']}]Import failed: {e}[/{COLORS['accent']}]")
        questionary.press_any_key_to_continue().ask()
        return

    if ok:
        targets = targets_used or [".claude/skills"]
        rows = "\n".join([f"- {project_dir.name} → {t}" for t in targets])
        console.print(
            f"[{COLORS['success']}]Imported '{selected.name}' to:[/{COLORS['success']}]\n{rows}"
        )
    else:
        console.print(f"[{COLORS['muted']}]Import cancelled.[/{COLORS['muted']}]")
    questionary.press_any_key_to_continue().ask()


@click.command()
@click.option("--config", "-c", default="config.yaml", type=click.Path(exists=True), help="Path to config.yaml")
def main(config: str) -> None:
    config_path = Path(config)
    cfg = _load_yaml(config_path)
    global CURRENT_CONFIG, CURRENT_TARGETS, TARGET_OPTIONS
    CURRENT_CONFIG = cfg
    default_target, opt_list, sel_list = _get_target_config(cfg)
    CURRENT_TARGETS = sel_list
    TARGET_OPTIONS = opt_list
    roots = get_project_roots(cfg)

    while True:
        _render_home(config_path, roots)

        choice = questionary.select(
            "Choose an action",
            choices=[
                questionary.Choice("Import skills into a project", value="import"),
                questionary.Choice("Settings: target folders & repo roots", value="settings"),
                questionary.Choice("Exit", value="exit"),
            ],
            style=custom_style,
        ).ask()

        if choice == "import":
            _import_flow(roots)
        elif choice == "settings":
            roots = _settings_menu(config_path, roots)
        elif choice == "exit" or choice is None:
            break


if __name__ == "__main__":
    main()
