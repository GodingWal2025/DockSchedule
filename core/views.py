import json
from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db import models
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import (
    Appointment, DriverVisit, Customer, Carrier,
    ProductType, Door, PITOperator, CapacityRule
)
from .forms import (
    AppointmentForm, AppointmentFilterForm, CheckInForm,
    CheckOutForm, KPIExportForm
)
from .utils import (
    get_dashboard_stats, appointment_to_export_row,
    generate_tsv_export, generate_csv_export,
    get_filtered_appointments, EXPORT_COLUMNS
)


# ─── Dashboard ───────────────────────────────────────────────────────────────

def dashboard(request):
    today = timezone.now().date()
    stats = get_dashboard_stats(today)
    context = {
        **stats,
        'today': today,
    }
    return render(request, 'dashboard.html', context)


# ─── Appointments ────────────────────────────────────────────────────────────

def add_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.status = 'Scheduled'
            appointment.save()
            return redirect('appointment_list')
    else:
        form = AppointmentForm()

    return render(request, 'appointment_add.html', {
        'form': form,
        'customers': Customer.objects.filter(active=True),
        'carriers': Carrier.objects.filter(active=True),
        'product_types': ProductType.objects.filter(active=True),
    })


def appointment_list(request):
    form = AppointmentFilterForm(request.GET or None)
    appointments = Appointment.objects.all().select_related(
        'customer', 'carrier', 'product_type'
    ).prefetch_related('visit')

    if form.is_valid():
        data = form.cleaned_data
        if data.get('date_from'):
            appointments = appointments.filter(appt_date__gte=data['date_from'])
        if data.get('date_to'):
            appointments = appointments.filter(appt_date__lte=data['date_to'])
        if data.get('appt_type'):
            appointments = appointments.filter(appt_type=data['appt_type'])
        if data.get('status'):
            appointments = appointments.filter(status=data['status'])
        if data.get('carrier'):
            appointments = appointments.filter(carrier=data['carrier'])
        if data.get('customer'):
            appointments = appointments.filter(customer=data['customer'])
        if data.get('search'):
            search = data['search'].strip()
            appointments = appointments.filter(
                models.Q(bol_shipment_no__icontains=search) |
                models.Q(carrier__name__icontains=search) |
                models.Q(customer__name__icontains=search) |
                models.Q(visit__visitor_name__icontains=search) |
                models.Q(visit__trailer_no__icontains=search)
            )

    appointments = appointments.order_by('-scheduled_datetime')

    return render(request, 'appointment_list.html', {
        'form': form,
        'appointments': appointments,
    })


def appointment_detail(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related(
            'customer', 'carrier', 'product_type'
        ).prefetch_related('visit'),
        pk=pk
    )
    return render(request, 'appointment_detail.html', {
        'appointment': appointment,
    })


# ─── Check-In ────────────────────────────────────────────────────────────────

def check_in(request):
    selected_appointment = None
    form = None

    # Handle BOL lookup
    search_bol = request.GET.get('bol', '').strip()
    if search_bol:
        try:
            selected_appointment = Appointment.objects.select_related(
                'customer', 'carrier', 'product_type'
            ).get(
                bol_shipment_no__iexact=search_bol,
                status='Scheduled'
            )
            form = CheckInForm()
        except Appointment.DoesNotExist:
            # Try partial match
            matches = Appointment.objects.select_related(
                'customer', 'carrier', 'product_type'
            ).filter(
                bol_shipment_no__icontains=search_bol,
                status='Scheduled'
            )
            if matches.count() == 1:
                selected_appointment = matches.first()
                form = CheckInForm()
            elif matches.count() > 1:
                return render(request, 'check_in.html', {
                    'search_bol': search_bol,
                    'bol_results': matches,
                })
            else:
                return render(request, 'check_in.html', {
                    'search_bol': search_bol,
                    'not_found': True,
                })

    # Handle form submission
    if request.method == 'POST' and 'appointment_id' in request.POST:
        appointment = get_object_or_404(Appointment, pk=request.POST['appointment_id'])
        form = CheckInForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.appointment = appointment
            visit.check_in_time = timezone.now()
            visit.in_out_status = 'In'

            # Calculate status
            new_status = appointment.calculate_status_on_checkin(visit.check_in_time)
            appointment.status = new_status

            visit.save()
            appointment.save()

            return redirect('dashboard')

    # Show currently scheduled appointments for selection
    scheduled = Appointment.objects.filter(
        status='Scheduled',
        appt_date=timezone.now().date()
    ).select_related('customer', 'carrier')

    return render(request, 'check_in.html', {
        'scheduled': scheduled,
        'selected_appointment': selected_appointment,
        'form': form,
        'search_bol': search_bol,
        'doors': Door.objects.filter(active=True, status='Open'),
        'operators': PITOperator.objects.filter(active=True),
    })


# ─── Check-Out ───────────────────────────────────────────────────────────────

def check_out(request):
    selected_visit = None

    # Handle BOL lookup
    search_bol = request.GET.get('bol', '').strip()
    if search_bol:
        try:
            appointment = Appointment.objects.get(
                bol_shipment_no__iexact=search_bol,
                status='Checked In'
            )
            selected_visit = appointment.visit
        except Appointment.DoesNotExist:
            matches = Appointment.objects.filter(
                bol_shipment_no__icontains=search_bol,
                status='Checked In'
            ).select_related('visit')
            if matches.count() == 1:
                selected_visit = matches.first().visit
            elif matches.count() > 1:
                return render(request, 'check_out.html', {
                    'search_bol': search_bol,
                    'bol_results': matches,
                })
            else:
                return render(request, 'check_out.html', {
                    'search_bol': search_bol,
                    'not_found': True,
                })

    # Handle form submission
    if request.method == 'POST' and 'visit_id' in request.POST:
        visit = get_object_or_404(
            DriverVisit.objects.select_related('appointment'),
            pk=request.POST['visit_id']
        )
        form = CheckOutForm(request.POST, instance=visit)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.check_out_time = timezone.now()
            visit.in_out_status = 'Out'
            visit.calculate_dwell_time()
            visit.save()

            # Update appointment status to Completed
            visit.appointment.status = 'Completed'
            visit.appointment.save()

            return redirect('dashboard')
    else:
        form = None
        if selected_visit:
            now = timezone.now()
            form = CheckOutForm(initial={
                'check_out_time': now.strftime('%Y-%m-%dT%H:%M')
            })

    # Show checked-in drivers
    checked_in = Appointment.objects.filter(
        status='Checked In'
    ).select_related(
        'customer', 'carrier', 'visit__assigned_door'
    )

    return render(request, 'check_out.html', {
        'checked_in': checked_in,
        'selected_visit': selected_visit,
        'form': form,
        'search_bol': search_bol,
    })


# ─── KPI Export ──────────────────────────────────────────────────────────────

def kpi_export(request):
    preview_data = []
    form = KPIExportForm(initial={
        'date_from': timezone.now().date() - timedelta(days=1),
        'date_to': timezone.now().date(),
    })

    if request.method == 'POST':
        form = KPIExportForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            qs = Appointment.objects.filter(
                appt_date__gte=data['date_from'],
                appt_date__lte=data['date_to']
            ).select_related(
                'customer', 'carrier', 'product_type'
            ).prefetch_related(
                'visit', 'visit__assigned_door', 'visit__pit_operator'
            )

            if data['appt_type'] != 'All':
                qs = qs.filter(appt_type=data['appt_type'])
            if data['status'] != 'All':
                qs = qs.filter(status=data['status'])

            # Filter by include flags
            status_filter = models.Q()
            if data.get('include_scheduled'):
                status_filter |= models.Q(status='Scheduled')
            if data.get('include_checked_in'):
                status_filter |= models.Q(status='Checked In')
            if data.get('include_completed'):
                status_filter |= models.Q(status='Completed')

            # Always include Early, On Time, Late (they're Checked In variants)
            if data.get('include_checked_in'):
                status_filter |= models.Q(status__in=['Early', 'On Time', 'Late'])

            if status_filter:
                qs = qs.filter(status_filter)

            # Handle export actions
            if 'copy_clipboard' in request.POST:
                tsv_data = generate_tsv_export(qs)
                return JsonResponse({'tsv': tsv_data})

            if 'download_csv' in request.POST:
                csv_data = generate_csv_export(qs)
                response = HttpResponse(csv_data, content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="kpi_export.csv"'
                return response

            # Build preview
            for appt in qs.order_by('scheduled_datetime'):
                preview_data.append(appointment_to_export_row(appt))

    return render(request, 'kpi_export.html', {
        'form': form,
        'preview_data': preview_data,
        'columns': EXPORT_COLUMNS,
    })


# ─── API Endpoints ───────────────────────────────────────────────────────────

def api_appointments(request):
    """JSON API for appointment search/filter."""
    appointments = Appointment.objects.all().select_related(
        'customer', 'carrier', 'product_type'
    ).prefetch_related('visit')

    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    appt_type = request.GET.get('appt_type', '').strip()
    date_str = request.GET.get('date', '').strip()

    if query:
        appointments = appointments.filter(
            models.Q(bol_shipment_no__icontains=query) |
            models.Q(customer__name__icontains=query) |
            models.Q(carrier__name__icontains=query) |
            models.Q(visit__visitor_name__icontains=query)
        )
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    if appt_type:
        appointments = appointments.filter(appt_type=appt_type)
    if date_str:
        appointments = appointments.filter(appt_date=date_str)

    data = []
    for appt in appointments[:50]:
        data.append({
            'id': appt.id,
            'appt_type': appt.appt_type,
            'appt_date': appt.appt_date.isoformat(),
            'appt_time': appt.appt_time.strftime('%H:%M'),
            'customer': appt.customer.name if appt.customer else None,
            'carrier': appt.carrier.name if appt.carrier else None,
            'status': appt.status,
            'bol_shipment_no': appt.bol_shipment_no,
        })
    return JsonResponse({'appointments': data})


def api_check_bol(request):
    """Check if a BOL number already exists."""
    bol = request.GET.get('bol', '').strip()
    exclude_id = request.GET.get('exclude_id')

    if not bol:
        return JsonResponse({'exists': False})

    qs = Appointment.objects.filter(bol_shipment_no__iexact=bol)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)

    exists = qs.exclude(status='Cancelled').exists()
    matches = []
    if exists:
        for appt in qs.exclude(status='Cancelled')[:5]:
            matches.append({
                'id': appt.id,
                'bol': appt.bol_shipment_no,
                'customer': appt.customer.name if appt.customer else '',
                'date': appt.appt_date.isoformat(),
                'status': appt.status,
            })

    return JsonResponse({'exists': exists, 'matches': matches})


def api_capacity_check(request):
    """Check appointment capacity for a date/time slot/type."""
    date_str = request.GET.get('date', '').strip()
    time_str = request.GET.get('time', '').strip()
    appt_type = request.GET.get('appt_type', '').strip()

    if not all([date_str, time_str, appt_type]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        check_time = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return JsonResponse({'error': 'Invalid date/time format'}, status=400)

    # Find capacity rule
    day_of_week = check_date.weekday()
    month = check_date.month

    # Try exact match first
    rule = CapacityRule.objects.filter(
        month=month,
        day_of_week=day_of_week,
        time_slot=check_time,
        appt_type__in=[appt_type, 'Both'],
        active=True
    ).first()

    # Try without month specificity
    if not rule:
        rule = CapacityRule.objects.filter(
            day_of_week=day_of_week,
            time_slot=check_time,
            appt_type__in=[appt_type, 'Both'],
            active=True
        ).first()

    max_capacity = rule.max_appointments if rule else 5

    # Count existing appointments for that slot
    existing = Appointment.objects.filter(
        appt_date=check_date,
        appt_time=check_time,
        appt_type=appt_type
    ).exclude(status='Cancelled').count()

    at_capacity = existing >= max_capacity

    return JsonResponse({
        'existing': existing,
        'max_capacity': max_capacity,
        'at_capacity': at_capacity,
        'remaining': max(0, max_capacity - existing),
    })


def api_appointment_stats(request):
    """Return dashboard stats as JSON."""
    date_str = request.GET.get('date')
    date = None
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    stats = get_dashboard_stats(date)
    return JsonResponse({
        'total': stats['total'],
        'checked_in': stats['checked_in'],
        'completed': stats['completed'],
        'late': stats['late'],
        'missed': stats['missed'],
        'ib_count': stats['ib_count'],
        'ob_count': stats['ob_count'],
    })
