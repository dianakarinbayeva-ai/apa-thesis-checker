from __future__ import annotations

import json
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def resolve_existing_path(base: Path, explicit: str | None, candidates: list[str], glob_pattern: str, label: str) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            path = base / explicit
        if path.exists():
            return path
        raise FileNotFoundError(f"未找到{label}文件: {path}")
    for candidate in candidates:
        path = base / candidate
        if path.exists():
            return path
    matches = sorted(base.glob(glob_pattern))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        preview = ", ".join(path.name for path in matches[:5])
        raise FileNotFoundError(
            f"自动匹配到多个{label}文件，请显式传入路径。候选包括: {preview}"
        )
    raise FileNotFoundError(f"未找到{label}文件。")


def load_registry(registry_path: Path) -> dict:
    return json.loads(registry_path.read_text(encoding="utf-8"))


def export_selected_rules(registry: dict, rule_ids: list[str], output_path: Path) -> list[dict]:
    rule_map = {rule["rule_id"]: rule for rule in registry["rules"]}
    rules = [rule_map[rule_id] for rule_id in rule_ids if rule_id in rule_map]
    output_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    return rules
