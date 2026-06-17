from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.models import Appointment, PITOperator, DriverVisit
from .models import PITTask, StagingLane, PickTask


def _get_session_operator(request):
    operator_id = request.session.get('pit_operator_id')
    if operator_id:
        try:
            return PITOperator.objects.get(pk=operator_id, active=True)
        except PITOperator.DoesNotExist:
            request.session.pop('pit_operator_id', None)
    return None


def _ensure_ib_tasks(request):
    """Auto-create PITTasks for checked-in IB appointments that don't have one."""
    checked_in_ib = Appointment.objects.filter(
        appt_type='IB',
        status='Checked In'
    ).exclude(pit_tasks__task_type='IB_Unload')

    for appt in checked_in_ib:
        PITTask.objects.create(
            appointment=appt,
            task_type='IB_Unload',
            status='Pending',
            product_info=f"{appt.customer.name} - {appt.product_type.name}"
        )


def _ensure_ob_tasks(request):
    """Auto-create PITTasks for checked-in OB appointments that don't have one."""
    checked_in_ob = Appointment.objects.filter(
        appt_type='OB',
        status='Checked In'
    ).exclude(pit_tasks__task_type='OB_Load')

    for appt in checked_in_ob:
        PITTask.objects.create(
            appointment=appt,
            task_type='OB_Load',
            status='Pending',
            product_info=f"{appt.customer.name} - {appt.product_type.name}"
        )


# ─── Operator Select ─────────────────────────────────────────────────────────

def operator_select(request):
    if request.method == 'POST':
        operator_id = request.POST.get('operator')
        if operator_id:
            request.session['pit_operator_id'] = int(operator_id)
            return redirect('pit_board')

    operators = PITOperator.objects.filter(active=True).order_by('name')
    return render(request, 'pit/select.html', {'operators': operators})


# ─── Task Board ──────────────────────────────────────────────────────────────

def task_board(request):
    operator = _get_session_operator(request)
    if not operator:
        return redirect('pit_select')

    _ensure_ib_tasks(request)
    _ensure_ob_tasks(request)

    # Counts for each quadrant
    ib_pending = PITTask.objects.filter(task_type='IB_Unload', status='Pending').count()
    ib_in_progress = PITTask.objects.filter(task_type='IB_Unload', status='In Progress').count()

    ob_pending = PITTask.objects.filter(task_type='OB_Load', status='Pending').count()
    ob_in_progress = PITTask.objects.filter(task_type='OB_Load', status='In Progress').count()

    putaway_pending = PITTask.objects.filter(task_type='Putaway', status='Pending').count()
    putaway_in_progress = PITTask.objects.filter(task_type='Putaway', status='In Progress').count()

    pick_pending = PickTask.objects.filter(status='Pending').count()
    pick_in_progress = PickTask.objects.filter(status='In Progress').count()

    return render(request, 'pit/board.html', {
        'operator': operator,
        'ib_pending': ib_pending,
        'ib_in_progress': ib_in_progress,
        'ob_pending': ob_pending,
        'ob_in_progress': ob_in_progress,
        'putaway_pending': putaway_pending,
        'putaway_in_progress': putaway_in_progress,
        'pick_pending': pick_pending,
        'pick_in_progress': pick_in_progress,
    })


# ─── Inbound ─────────────────────────────────────────────────────────────────

def inbound_list(request):
    operator = _get_session_operator(request)
    if not operator:
        return redirect('pit_select')

    _ensure_ib_tasks(request)

    tasks = PITTask.objects.filter(
        task_type='IB_Unload'
    ).select_related('appointment', 'appointment__customer', 'appointment__product_type', 'operator').order_by('status', 'created_at')

    return render(request, 'pit/inbound_list.html', {
        'operator': operator,
        'tasks': tasks,
    })


def inbound_work(request, task_id):
    operator = _get_session_operator(request)
    if not operator:
        return redirect('pit_select')

    task = get_object_or_404(
        PITTask.objects.select_related(
            'appointment', 'appointment__customer', 'appointment__carrier',
            'appointment__product_type', 'appointment__visit__assigned_door',
            'operator'
        ),
        pk=task_id,
        task_type='IB_Unload'
    )

    return render(request, 'pit/inbound_work.html', {
        'operator': operator,
        'task': task,
    })


# ─── Outbound ────────────────────────────────────────────────────────────────

def outbound_list(request):
    operator = _get_session_operator(request)
    if not operator:
        return redirect('pit_select')

    _ensure_ob_tasks(request)

    tasks = PITTask.objects.filter(
        task_type='OB_Load'
    ).select_related('appointment', 'appointment__customer', 'appointment__product_type', 'operator').order_by('status', 'created_at')

    return render(request, 'pit/outbound_list.html', {
        'operator': operator,
        'tasks': tasks,
    })


def outbound_work(request, task_id):
    operator = _get_session_operator(request)
    if not operator:
        return redirect('pit_select')

    task = get_object_or_404(
        PITTask.objects.select_related(
            'appointment', 'appointment__customer', 'appointment__carrier',
            'appointment__product_type', 'appointment__visit__assigned_door',
            'operator'
        ),
        pk=task_id,
        task_type='OB_Load'
    )

    return render(request, 'pit/outbound_work.html', {
        'operator': operator,
        'task': task,
    })


# ─── Putaway ─────────────────────────────────────────────────────────────────

def putaway_list(request):
    operator = _get_session_operator(request)
    if not operator:
        return redirect('pit_select')

    tasks = PITTask.objects.filter(
        task_type='Putaway'
    ).select_related('appointment', 'appointment__customer', 'appointment__product_type', 'operator').order_by('status', 'created_at')

    return render(request, 'pit/putaway_list.html', {
        'operator': operator,
        'tasks': tasks,
    })


def putaway_work(request, task_id):
    operator = _get_session_operator(request)
    if not operator:
        return redirect('pit_select')

    task = get_object_or_404(
        PITTask.objects.select_related(
            'appointment', 'appointment__customer',
            'appointment__product_type', 'staging_lane', 'operator'
        ),
        pk=task_id,
        task_type='Putaway'
    )

    lanes = StagingLane.objects.filter(active=True)

    return render(request, 'pit/putaway_work.html', {
        'operator': operator,
        'task': task,
        'lanes': lanes,
    })


# ─── Pick ────────────────────────────────────────────────────────────────────

def pick_list(request):
    operator = _get_session_operator(request)
    if not operator:
        return redirect('pit_select')

    tasks = PickTask.objects.filter(
        status__in=['Pending', 'In Progress']
    ).select_related('customer', 'product_type', 'staging_lane', 'operator')

    return render(request, 'pit/pick_list.html', {
        'operator': operator,
        'tasks': tasks,
    })


def pick_work(request, task_id):
    operator = _get_session_operator(request)
    if not operator:
        return redirect('pit_select')

    task = get_object_or_404(
        PickTask.objects.select_related(
            'customer', 'product_type', 'staging_lane', 'operator'
        ),
        pk=task_id
    )

    return render(request, 'pit/pick_work.html', {
        'operator': operator,
        'task': task,
    })


# ─── AJAX Actions ────────────────────────────────────────────────────────────

@require_POST
def start_task(request, task_id):
    """Start any PITTask (IB, OB, Putaway)."""
    operator = _get_session_operator(request)
    if not operator:
        return JsonResponse({'error': 'No operator'}, status=403)

    task = get_object_or_404(PITTask, pk=task_id)
    task.start(operator)

    return JsonResponse({
        'status': task.status,
        'started_at': task.started_at.isoformat() if task.started_at else None,
        'operator': task.operator.name if task.operator else None,
    })


@require_POST
def complete_task(request, task_id):
    """Complete IB or OB task — auto-checks driver out."""
    operator = _get_session_operator(request)
    if not operator:
        return JsonResponse({'error': 'No operator'}, status=403)

    task = get_object_or_404(PITTask, pk=task_id)

    # Putaway uses staging_lane from form
    if request.POST.get('staging_lane'):
        try:
            task.staging_lane = StagingLane.objects.get(pk=request.POST['staging_lane'])
        except StagingLane.DoesNotExist:
            pass

    task.complete()

    return JsonResponse({
        'status': task.status,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'duration': task.duration_display,
        'auto_checkout': task.auto_checkout_triggered,
        'putaway_created': task.task_type == 'IB_Unload',
    })


@require_POST
def complete_putaway(request, task_id):
    """Complete a putaway task."""
    operator = _get_session_operator(request)
    if not operator:
        return JsonResponse({'error': 'No operator'}, status=403)

    task = get_object_or_404(PITTask, pk=task_id, task_type='Putaway')

    lane_id = request.POST.get('staging_lane')
    if lane_id:
        try:
            task.staging_lane = StagingLane.objects.get(pk=lane_id)
        except StagingLane.DoesNotExist:
            return JsonResponse({'error': 'Invalid lane'}, status=400)
    else:
        return JsonResponse({'error': 'Staging lane required'}, status=400)

    task.complete()

    return JsonResponse({
        'status': task.status,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'duration': task.duration_display,
        'staging_lane': task.staging_lane.lane_name if task.staging_lane else None,
    })


@require_POST
def start_pick(request, task_id):
    """Start a pick task."""
    operator = _get_session_operator(request)
    if not operator:
        return JsonResponse({'error': 'No operator'}, status=403)

    task = get_object_or_404(PickTask, pk=task_id)
    task.start(operator)

    return JsonResponse({
        'status': task.status,
        'started_at': task.started_at.isoformat() if task.started_at else None,
        'operator': task.operator.name if task.operator else None,
    })


@require_POST
def complete_pick(request, task_id):
    """Complete a pick task."""
    operator = _get_session_operator(request)
    if not operator:
        return JsonResponse({'error': 'No operator'}, status=403)

    task = get_object_or_404(PickTask, pk=task_id)
    task.complete()

    return JsonResponse({
        'status': task.status,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'duration': task.duration_display,
    })
