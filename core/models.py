from django.db import models
from django.utils import timezone


class Customer(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Carrier(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Door(models.Model):
    DOOR_DIRECTIONS = [
        ('IB', 'Inbound'),
        ('OB', 'Outbound'),
        ('Both', 'Both'),
    ]
    DOOR_STATUSES = [
        ('Open', 'Open'),
        ('Occupied', 'Occupied'),
        ('Closed', 'Closed'),
    ]

    door_name = models.CharField(max_length=50)
    area = models.CharField(max_length=100, blank=True)
    direction = models.CharField(max_length=10, choices=DOOR_DIRECTIONS, default='Both')
    status = models.CharField(max_length=20, choices=DOOR_STATUSES, default='Open')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['door_name']

    def __str__(self):
        return self.door_name


class PITOperator(models.Model):
    name = models.CharField(max_length=200)
    initials = models.CharField(max_length=10, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.initials})" if self.initials else self.name

    @property
    def display_name(self):
        return self.name


class Appointment(models.Model):
    APPT_TYPE_CHOICES = [
        ('IB', 'Inbound'),
        ('OB', 'Outbound'),
    ]
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Checked In', 'Checked In'),
        ('Completed', 'Completed'),
        ('Late', 'Late'),
        ('Missed', 'Missed'),
        ('Cancelled', 'Cancelled'),
    ]

    appt_type = models.CharField(max_length=2, choices=APPT_TYPE_CHOICES)
    appt_date = models.DateField()
    appt_time = models.TimeField()
    scheduled_datetime = models.DateTimeField()
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT)
    carrier = models.ForeignKey(Carrier, on_delete=models.PROTECT)
    bol_shipment_no = models.CharField(max_length=100, blank=True)
    delivery_no = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['scheduled_datetime']

    def __str__(self):
        return f"{self.appt_type} - {self.customer.name} - {self.scheduled_datetime.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        from datetime import datetime
        self.scheduled_datetime = datetime.combine(self.appt_date, self.appt_time)
        super().save(*args, **kwargs)

    @property
    def is_missed(self):
        """Check if appointment should be marked as missed."""
        now = timezone.now()
        scheduled = self.scheduled_datetime
        if isinstance(scheduled, str):
            scheduled = timezone.make_aware(
                datetime.strptime(scheduled, '%Y-%m-%d %H:%M:%S')
            )
        if self.status in ['Scheduled', 'Late'] and now > scheduled:
            try:
                if not hasattr(self, 'visit') or not self.visit.check_in_time:
                    return True
            except DriverVisit.DoesNotExist:
                return True
        return False

    def calculate_status_on_checkin(self, check_in_time):
        """Calculate Early, On Time, or Late based on check-in time."""
        from datetime import timedelta
        diff = check_in_time - self.scheduled_datetime
        minutes = diff.total_seconds() / 60

        if minutes < -15:
            return 'Early'
        elif -15 <= minutes <= 15:
            return 'On Time'
        else:
            return 'Late'


class DriverVisit(models.Model):
    LOAD_LOCK_CHOICES = [
        ('Y', 'Yes'),
        ('N', 'No'),
        ('NA', 'N/A'),
    ]
    INOUT_CHOICES = [
        ('In', 'In'),
        ('Out', 'Out'),
    ]

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='visit'
    )
    visitor_name = models.CharField(max_length=200, blank=True)
    trailer_no = models.CharField(max_length=100, blank=True)
    drivers_license_state = models.CharField(max_length=50, blank=True)
    load_lock = models.CharField(max_length=2, choices=LOAD_LOCK_CHOICES, blank=True)
    assigned_door = models.ForeignKey(
        Door,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    pit_operator = models.ForeignKey(
        PITOperator,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    dwell_seconds = models.PositiveIntegerField(null=True, blank=True)
    in_out_status = models.CharField(max_length=3, choices=INOUT_CHOICES, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Visit for {self.appointment}"

    def calculate_dwell_time(self):
        """Calculate dwell time in seconds and format as HH:MM:SS."""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            self.dwell_seconds = int(delta.total_seconds())
            return self.dwell_seconds
        return None

    @property
    def dwell_time_display(self):
        """Return dwell time as HH:MM:SS string."""
        if self.dwell_seconds is not None:
            hours, remainder = divmod(self.dwell_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return ""


class CapacityRule(models.Model):
    MONTH_CHOICES = [(i, i) for i in range(1, 13)]
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    APPT_TYPE_CHOICES = [
        ('IB', 'Inbound'),
        ('OB', 'Outbound'),
        ('Both', 'Both'),
    ]

    month = models.PositiveSmallIntegerField(choices=MONTH_CHOICES)
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    time_slot = models.TimeField()
    appt_type = models.CharField(max_length=10, choices=APPT_TYPE_CHOICES, default='Both')
    max_appointments = models.PositiveSmallIntegerField(default=5)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['month', 'day_of_week', 'time_slot', 'appt_type']

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.time_slot} - {self.appt_type}: {self.max_appointments}"


class AuditLog(models.Model):
    ACTIONS = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('CHECKIN', 'Check In'),
        ('CHECKOUT', 'Check Out'),
        ('CANCEL', 'Cancel'),
    ]

    user_id = models.CharField(max_length=100, blank=True)
    action = models.CharField(max_length=20, choices=ACTIONS)
    record_type = models.CharField(max_length=50)
    record_id = models.PositiveIntegerField()
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
