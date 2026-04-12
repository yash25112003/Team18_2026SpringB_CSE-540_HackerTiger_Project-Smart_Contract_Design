from django.core.management.base import BaseCommand

from deploy.models import Block


class Command(BaseCommand):
    help = "Delete every Block record. Use with caution."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete blocks without asking for confirmation.",
        )

    def handle(self, *args, **options):
        force_delete = options["force"]
        total_blocks = Block.objects.count()

        if total_blocks == 0:
            self.stdout.write(self.style.WARNING("No blocks to delete."))
            return

        if not force_delete:
            confirm = input(
                f"This will delete {total_blocks} block(s). Type 'DELETE' to confirm: "
            )
            if confirm.strip().upper() != "DELETE":
                self.stdout.write(self.style.WARNING("Aborted. No blocks were deleted."))
                return

        deleted, _ = Block.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {deleted} block object(s).")
        )
