"""Utility functions for export and data processing."""
import csv
import io
from datetime import datetime, timedelta


def time_to_excel_fraction(t):
    """Convert a time object to Excel-style time fraction."""
    if not t:
        return ''
    return t.hour / 24 + t.minute / 1440


def format_datetime_for_excel(dt):
    """Format datetime as M/D/YYYY H:MM AM/PM."""
    if not dt:
        return ''
    return dt.strftime('%-m/%-d/%Y %-I:%M %p')


def format_dwell_time(seconds):
    """Format seconds as HH:MM:SS."""
    if seconds is None:
        return ''
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def appointment_to_export_row(appointment):
    """Convert an appointment to a KPI export row dict."""
    visit = getattr(appointment, 'visit', None)

    row = {
        'Appt_Type': appointment.appt_type,
        'In': format_datetime_for_excel(visit.check_in_time) if visit else '',
        'Out': format_datetime_for_excel(visit.check_out_time) if visit else '',
        'Appt_Time': format_datetime_for_excel(appointment.scheduled_datetime),
        'Status': appointment.status,
        'Customer': appointment.customer.name if appointment.customer else '',
        'Type': appointment.product_type.name if appointment.product_type else '',
        'Carrier': appointment.carrier.name if appointment.carrier else '',
        'BOL-Shipment_No': appointment.bol_shipment_no,
        'Visitor_Name': visit.visitor_name if visit else '',
        'Delivery_No': appointment.delivery_no,
        'Trailer_No': visit.trailer_no if visit else '',
        'Drivers_License_State': visit.drivers_license_state if visit else '',
        'Load_Lock': visit.load_lock if visit else '',
        'Assigned_Door': visit.assigned_door.door_name if visit and visit.assigned_door else '',
        'Dwell_Time': format_dwell_time(visit.dwell_seconds) if visit else '',
        'Notes': (appointment.notes or '') + (' ' + visit.notes if visit and visit.notes else ''),
        'PIT_Operator': visit.pit_operator.name if visit and visit.pit_operator else '',
        'InOutStatus': visit.in_out_status if visit else '',
        'Color_Coding': '',
        'Appt_Day': appointment.appt_date.strftime('%A') if appointment.appt_date else '',
        'Appt_Slot': time_to_excel_fraction(appointment.appt_time),
        'Appt_Month': appointment.appt_date.month if appointment.appt_date else '',
        'Appt_Year': appointment.appt_date.year if appointment.appt_date else '',
    }
    return row


EXPORT_COLUMNS = [
    'Appt_Type', 'In', 'Out', 'Appt_Time', 'Status',
    'Customer', 'Type', 'Carrier', 'BOL-Shipment_No',
    'Visitor_Name', 'Delivery_No', 'Trailer_No',
    'Drivers_License_State', 'Load_Lock', 'Assigned_Door',
    'Dwell_Time', 'Notes', 'PIT_Operator', 'InOutStatus',
    'Color_Coding', 'Appt_Day', 'Appt_Slot', 'Appt_Month', 'Appt_Year'
]


def generate_tsv_export(appointments):
    """Generate tab-separated export string from appointments."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=EXPORT_COLUMNS,
        delimiter='\t',
        lineterminator='\n',
        quoting=csv.QUOTE_MINIMAL
    )
    writer.writeheader()
    for appt in appointments:
        row = appointment_to_export_row(appt)
        writer.writerow(row)
    return output.getvalue()


def generate_csv_export(appointments):
    """Generate CSV export string from appointments."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=EXPORT_COLUMNS,
        lineterminator='\n'
    )
    writer.writeheader()
    for appt in appointments:
        row = appointment_to_export_row(appt)
        writer.writerow(row)
    return output.getvalue()


def get_dashboard_stats(date=None):
    """Get dashboard statistics for a given date (defaults to today)."""
    from django.utils import timezone
    from .models import Appointment

    if date is None:
        date = timezone.now().date()

    today_appointments = Appointment.objects.filter(appt_date=date)
    checked_in = today_appointments.filter(status='Checked In')
    completed = today_appointments.filter(status='Completed')
    late = today_appointments.filter(status='Late')
    missed = today_appointments.filter(status='Missed')
    cancelled = today_appointments.filter(status='Cancelled')
    ib_count = today_appointments.filter(appt_type='IB').count()
    ob_count = today_appointments.filter(appt_type='OB').count()

    return {
        'total': today_appointments.count(),
        'checked_in': checked_in.count(),
        'completed': completed.count(),
        'late': late.count(),
        'missed': missed.count(),
        'cancelled': cancelled.count(),
        'ib_count': ib_count,
        'ob_count': ob_count,
        'scheduled_list': today_appointments.filter(
            status__in=['Scheduled']
        ).select_related('customer', 'carrier'),
        'checked_in_list': today_appointments.filter(
            status='Checked In'
        ).select_related('customer', 'carrier', 'visit__assigned_door'),
    }


def get_filtered_appointments(form_data):
    """Get appointments filtered by form data."""
    from .models import Appointment

    qs = Appointment.objects.all().select_related(
        'customer', 'carrier', 'product_type',
        'visit__assigned_door', 'visit__pit_operator'
    )

    date_from = form_data.get('date_from')
    date_to = form_data.get('date_to')
    appt_type = form_data.get('appt_type')
    status = form_data.get('status')
    carrier = form_data.get('carrier')
    customer = form_data.get('customer')
    search = form_data.get('search', '').strip()

    if date_from:
        qs = qs.filter(appt_date__gte=date_from)
    if date_to:
        qs = qs.filter(appt_date__lte=date_to)
    if appt_type:
        qs = qs.filter(appt_type=appt_type)
    if status:
        qs = qs.filter(status=status)
    if carrier:
        qs = qs.filter(carrier=carrier)
    if customer:
        qs = qs.filter(customer=customer)
    if search:
        qs = qs.filter(
            models.Q(bol_shipment_no__icontains=search) |
            models.Q(carrier__name__icontains=search) |
            models.Q(customer__name__icontains=search) |
            models.Q(visit__visitor_name__icontains=search) |
            models.Q(visit__trailer_no__icontains=search)
        )

    return qs
