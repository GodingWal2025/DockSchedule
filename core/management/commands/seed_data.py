from django.core.management.base import BaseCommand
from core.models import Customer, Carrier, ProductType, Door, PITOperator, CapacityRule


class Command(BaseCommand):
    help = 'Seed reference data for the driver log system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding reference data...')

        # Customers
        customers = [
            'ABC Corp', 'XYZ Logistics', 'Global Freight',
            'FastShip Inc', 'Metro Supply', 'Premier Distribution',
            'Summit Transport', 'Coastal Cargo'
        ]
        for name in customers:
            Customer.objects.get_or_create(name=name, defaults={'active': True})
        self.stdout.write(f'  {len(customers)} customers')

        # Carriers
        carriers = [
            'FedEx Freight', 'UPS Freight', 'XPO Logistics',
            'Old Dominion', 'Estes Express', 'R+L Carriers',
            'ABF Freight', 'YRC Worldwide', 'Saia LTL Freight',
            'Dayton Freight'
        ]
        for name in carriers:
            Carrier.objects.get_or_create(name=name, defaults={'active': True})
        self.stdout.write(f'  {len(carriers)} carriers')

        # Product Types
        product_types = [
            'Dry Goods', 'Frozen', 'Hazmat', 'Oversized',
            'Electronics', 'Pharmaceutical', 'Automotive Parts',
            'Food & Beverage', 'Textiles', 'Chemicals'
        ]
        for name in product_types:
            ProductType.objects.get_or_create(name=name, defaults={'active': True})
        self.stdout.write(f'  {len(product_types)} product types')

        # Doors
        doors = [
            ('D01', 'Main Dock', 'Both'),
            ('D02', 'Main Dock', 'Both'),
            ('D03', 'Main Dock', 'Both'),
            ('D04', 'Main Dock', 'Both'),
            ('D05', 'East Wing', 'IB'),
            ('D06', 'East Wing', 'IB'),
            ('D07', 'West Wing', 'OB'),
            ('D08', 'West Wing', 'OB'),
            ('D09', 'Cold Storage', 'Both'),
            ('D10', 'Oversized', 'Both'),
        ]
        for door_name, area, direction in doors:
            Door.objects.get_or_create(
                door_name=door_name,
                defaults={'area': area, 'direction': direction, 'status': 'Open', 'active': True}
            )
        self.stdout.write(f'  {len(doors)} doors')

        # PIT Operators
        operators = [
            ('John Smith', 'JS'),
            ('Maria Garcia', 'MG'),
            ('Bob Johnson', 'BJ'),
            ('Lisa Chen', 'LC'),
            ('David Park', 'DP'),
            ('Angela Rodriguez', 'AR'),
        ]
        for name, initials in operators:
            PITOperator.objects.get_or_create(
                name=name,
                defaults={'initials': initials, 'active': True}
            )
        self.stdout.write(f'  {len(operators)} PIT operators')

        # Capacity Rules - default 5 per slot for all days/times
        time_slots = [
            (6, 0), (7, 0), (8, 0), (9, 0), (10, 0),
            (11, 0), (12, 0), (13, 0), (14, 0), (15, 0),
            (16, 0), (17, 0), (18, 0)
        ]
        days = range(0, 5)  # Monday through Friday
        months = range(1, 13)
        appt_types = ['IB', 'OB']

        count = 0
        for month in months:
            for day in days:
                for hour, minute in time_slots:
                    for appt_type in appt_types:
                        from datetime import time
                        CapacityRule.objects.get_or_create(
                            month=month,
                            day_of_week=day,
                            time_slot=time(hour, minute),
                            appt_type=appt_type,
                            defaults={'max_appointments': 5, 'active': True}
                        )
                        count += 1
        self.stdout.write(f'  {count} capacity rules')

        self.stdout.write(self.style.SUCCESS('Done! Reference data seeded.'))
