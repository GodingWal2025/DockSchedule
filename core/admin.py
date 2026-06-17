from django.contrib import admin
from .models import (
    Customer, Carrier, ProductType, Door, PITOperator,
    Appointment, DriverVisit, CapacityRule, AuditLog
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'active']
    list_filter = ['active']
    search_fields = ['name']


@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name', 'active']
    list_filter = ['active']
    search_fields = ['name']


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'active']
    list_filter = ['active']
    search_fields = ['name']


@admin.register(Door)
class DoorAdmin(admin.ModelAdmin):
    list_display = ['door_name', 'area', 'direction', 'status', 'active']
    list_filter = ['direction', 'status', 'active']
    search_fields = ['door_name']


@admin.register(PITOperator)
class PITOperatorAdmin(admin.ModelAdmin):
    list_display = ['name', 'initials', 'active']
    list_filter = ['active']
    search_fields = ['name', 'initials']


class DriverVisitInline(admin.StackedInline):
    model = DriverVisit
    can_delete = False
    extra = 0


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'appt_type', 'customer', 'carrier', 'scheduled_datetime',
        'status', 'bol_shipment_no', 'created_at'
    ]
    list_filter = ['appt_type', 'status', 'appt_date']
    search_fields = [
        'bol_shipment_no', 'customer__name', 'carrier__name',
        'delivery_no', 'visit__visitor_name'
    ]
    date_hierarchy = 'appt_date'
    inlines = [DriverVisitInline]


@admin.register(DriverVisit)
class DriverVisitAdmin(admin.ModelAdmin):
    list_display = [
        'appointment', 'visitor_name', 'trailer_no',
        'assigned_door', 'check_in_time', 'check_out_time',
        'dwell_time_display'
    ]
    list_filter = ['check_in_time', 'assigned_door']
    search_fields = [
        'visitor_name', 'trailer_no', 'appointment__bol_shipment_no'
    ]


@admin.register(CapacityRule)
class CapacityRuleAdmin(admin.ModelAdmin):
    list_display = [
        'month', 'get_day_of_week_display', 'time_slot',
        'appt_type', 'max_appointments', 'active'
    ]
    list_filter = ['month', 'day_of_week', 'appt_type', 'active']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'record_type', 'record_id', 'user_id', 'timestamp']
    list_filter = ['action', 'record_type']
    readonly_fields = [
        'user_id', 'action', 'record_type', 'record_id',
        'old_value', 'new_value', 'timestamp'
    ]
