from django.core.management.base import BaseCommand

from apps.hoarder.models import Category


class Command(BaseCommand):
    help = "Re-apply each category's preprocessors to its existing hoards."

    def handle(self, **options):
        for category in Category.objects.prefetch_related("hoards"):
            changed = 0
            for hoard in category.hoards.all():
                data = category.preprocess(hoard.data)
                if data != hoard.data:
                    hoard.data = data
                    hoard.save(update_fields=["data"])
                    changed += 1
            self.stdout.write(
                f"{category.slug}: {changed}/{category.hoards.count()} hoards updated"
            )
