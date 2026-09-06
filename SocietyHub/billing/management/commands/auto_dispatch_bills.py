import datetime
from django.core.management.base import BaseCommand
from SocietyHub.users.models import Society
from SocietyHub.billing.models import MaintenanceScheduleConfig
from SocietyHub.billing.utils import execute_auto_dispatch_for_society, get_or_create_schedule_config

class Command(BaseCommand):
    help = (
        "Automatically generates and dispatches itemized CHS maintenance bills "
        "to all approved residents on the designated recurring calendar date."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force bill dispatch regardless of scheduled day or existing bills for the cycle',
        )
        parser.add_argument(
            '--society_id',
            type=int,
            help='Specific society ID to process (defaults to all approved societies)',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Target evaluation date in YYYY-MM-DD format (defaults to today)',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        society_id = options.get('society_id')
        date_str = options.get('date')

        target_date = datetime.date.today()
        if date_str:
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Invalid date format '{date_str}'. Use YYYY-MM-DD."))
                return

        self.stdout.write(self.style.NOTICE(f"==> Evaluating auto-dispatch for date: {target_date} (Force={force})"))

        societies = Society.objects.filter(is_approved=True)
        if society_id:
            societies = societies.filter(id=society_id)

        if not societies.exists():
            self.stdout.write(self.style.WARNING("No approved societies found to process."))
            return

        total_processed = 0
        total_dispatched_societies = 0

        for society in societies:
            total_processed += 1
            config = get_or_create_schedule_config(society)
            next_date = config.get_next_dispatch_date(target_date)

            res = execute_auto_dispatch_for_society(society, ref_date=target_date, force=force)
            safe_reason = str(res.get('reason', '')).replace('\u20b9', 'Rs.')
            if res.get('dispatched'):
                total_dispatched_societies += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[SUCCESS] {society.name}: {safe_reason}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"[SKIPPED] {society.name}: {safe_reason} (Next Scheduled: {next_date})"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"==> Completed auto-dispatch cycle: {total_dispatched_societies}/{total_processed} societies dispatched."
            )
        )
