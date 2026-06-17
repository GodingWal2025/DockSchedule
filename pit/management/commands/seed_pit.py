from django.core.management.base import BaseCommand
from pit.models import StagingLane


class Command(BaseCommand):
    help = 'Seed PIT app reference data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding PIT data...')

        lanes = [
            ('SL-A1', 'Dry Goods'),
            ('SL-A2', 'Dry Goods'),
            ('SL-A3', 'Dry Goods'),
            ('SL-B1', 'Cold Storage'),
            ('SL-B2', 'Cold Storage'),
            ('SL-C1', 'Hazmat'),
            ('SL-D1', 'Oversized'),
            ('SL-D2', 'Oversized'),
            ('SL-E1', 'Electronics'),
            ('SL-E2', 'Electronics'),
            ('SL-F1', 'Pharmaceutical'),
            ('SL-G1', 'Automotive'),
            ('SL-H1', 'General'),
            ('SL-H2', 'General'),
            ('SL-H3', 'General'),
        ]
        for lane_name, area in lanes:
            StagingLane.objects.get_or_create(
                lane_name=lane_name,
                defaults={'area': area, 'active': True}
            )
        self.stdout.write(f'  {len(lanes)} staging lanes')

        self.stdout.write(self.style.SUCCESS('Done! PIT data seeded.'))
