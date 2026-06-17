from django.db import models
from django.utils import timezone
from core.models import Appointment, PITOperator, Customer, ProductType


class StagingLane(models.Model):
    lane_name = models.CharField(max_length=20)
    area = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['lane_name']

    def __str__(self):
        return self.lane_name


class PITTask(models.Model):
    TASK_TYPES = [
        ('IB_Unload', 'Inbound Unload'),
        ('OB_Load', 'Outbound Load'),
        ('Putaway', 'Putaway'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pit_tasks'
    )
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    operator = models.ForeignKey(
        PITOperator,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    staging_lane = models.ForeignKey(
        StagingLane,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    product_info = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    auto_checkout_triggered = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task_type} - {self.status}"

    def start(self, operator):
        self.operator = operator
        self.status = 'In Progress'
        self.started_at = timezone.now()
        self.save()

    def complete(self):
        self.status = 'Completed'
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())

        # Auto check-out for Inbound/Outbound
        if self.task_type in ('IB_Unload', 'OB_Load') and self.appointment:
            try:
                from core.models import DriverVisit
                visit = self.appointment.visit
                visit.check_out_time = timezone.now()
                visit.in_out_status = 'Out'
                visit.calculate_dwell_time()
                visit.save()
                self.appointment.status = 'Completed'
                self.appointment.save()
                self.auto_checkout_triggered = True

                # Auto-create Putaway task for Inbound
                if self.task_type == 'IB_Unload':
                    PITTask.objects.create(
                        appointment=self.appointment,
                        task_type='Putaway',
                        status='Pending',
                        product_info=self.product_info or f"{self.appointment.customer.name} - {self.appointment.product_type.name}"
                    )
            except Exception:
                pass

        self.save()

    @property
    def duration_display(self):
        if self.duration_seconds:
            m, s = divmod(self.duration_seconds, 60)
            h, m = divmod(m, 60)
            if h > 0:
                return f"{h}:{m:02d}:{s:02d}"
            return f"{m}:{s:02d}"
        return "--:--"


class PickTask(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Normal', 'Normal'),
        ('Low', 'Low'),
    ]

    pick_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Normal')
    from_location = models.CharField(max_length=100, blank=True)
    staging_lane = models.ForeignKey(
        StagingLane,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    operator = models.ForeignKey(
        PITOperator,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    created_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f"Pick {self.pick_number} - {self.status}"

    def start(self, operator):
        self.operator = operator
        self.status = 'In Progress'
        self.started_at = timezone.now()
        self.save()

    def complete(self):
        self.status = 'Completed'
        self.completed_at = timezone.now()
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        self.save()

    @property
    def duration_display(self):
        if self.duration_seconds:
            m, s = divmod(self.duration_seconds, 60)
            h, m = divmod(m, 60)
            if h > 0:
                return f"{h}:{m:02d}:{s:02d}"
            return f"{m}:{s:02d}"
        return "--:--"
