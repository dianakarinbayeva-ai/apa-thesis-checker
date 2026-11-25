from django.db import migrations


def seed_groups(apps, schema_editor):
    Group = apps.get_model("platform_app", "StudyGroup")
    for number in (1, 2):
        Group.objects.get_or_create(code=f"empa-2025-winter-{number}", defaults={
            "programme": "Executive MPA–2025", "programme_code": "7М04120",
            "group_number": number, "intake": "winter", "year": 2025})


class Migration(migrations.Migration):
    dependencies = [("platform_app", "0002_curator_rosters")]
    operations = [migrations.RunPython(seed_groups, migrations.RunPython.noop)]
