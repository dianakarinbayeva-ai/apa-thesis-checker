"""Import an authorized private roster from JSON; never bundle the input."""
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from platform_app.models import StudyGroup, RosterStudent


class Command(BaseCommand):
    help = "Import private roster JSON: groups[{code, students:[full_name, ...]}]. Existing rows are preserved."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            path = Path(options["path"])
            if path.stat().st_size > 2 * 1024 * 1024:
                raise ValueError("Roster exceeds 2 MB")
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict) or not isinstance(data.get("groups"), list) or not data["groups"]:
                raise ValueError("Expected a nonempty groups list")
            prepared, seen = [], set()
            for item in data["groups"]:
                if not isinstance(item, dict) or item.get("code") in seen:
                    raise ValueError("Invalid or repeated group")
                group = StudyGroup.objects.get(code=item["code"])
                seen.add(group.code)
                students = item.get("students")
                if not isinstance(students, list) or not 1 <= len(students) <= 1000:
                    raise ValueError("Expected 1–1000 student names")
                if any(not isinstance(name, str) or not name.strip() or len(name.strip()) > 180 for name in students):
                    raise ValueError("Invalid student name")
                prepared.append((group, [name.strip() for name in students]))
            total = 0
            with transaction.atomic():
                for group, names in prepared:
                    existing = {s.position:s for s in RosterStudent.objects.select_for_update().filter(group=group)}
                    if any(pos > len(names) or row.full_name != names[pos-1] for pos, row in existing.items()):
                        raise ValueError("Roster conflict; no existing student will be replaced")
                    for position, name in enumerate(names, 1):
                        if position not in existing:
                            RosterStudent.objects.create(group=group, position=position, full_name=name)
                    group.roster_loaded = True
                    group.save(update_fields=["roster_loaded"])
                    total += len(names)
                if options["dry_run"]:
                    transaction.set_rollback(True)
            self.stdout.write(self.style.SUCCESS(f"Validated {len(prepared)} groups and {total} students" +
                (" (dry run; not saved)" if options["dry_run"] else "")))
        except (OSError, ValueError, KeyError, TypeError, StudyGroup.DoesNotExist) as exc:
            raise CommandError(str(exc)) from exc
