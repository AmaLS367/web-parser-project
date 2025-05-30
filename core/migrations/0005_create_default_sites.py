from django.db import migrations

def create_default_sites(apps, schema_editor):
    BookingSite = apps.get_model('core', 'BookingSite')

    default_sites = [
        ("Padel39", "https://www.padel39.com/"),
        ("Padel Club Austin", "https://www.padelclubaustin.com/"),
        ("The King of Padel", "https://www.krakenpadelclub.com/"),
        ("UPadel", "https://upadel.us/"),
    ]

    for name, url in default_sites:
        BookingSite.objects.get_or_create(name=name, defaults={"url": url, "is_active": True})

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_alter_slot_end_time_alter_slot_start_time"),
    ]

    operations = [
        migrations.RunPython(create_default_sites),
    ]

