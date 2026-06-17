from django import forms
from .models import Appointment, DriverVisit, Customer, Carrier, ProductType, Door, PITOperator


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'appt_type', 'appt_date', 'appt_time',
            'customer', 'product_type', 'carrier',
            'bol_shipment_no', 'delivery_no', 'notes'
        ]
        widgets = {
            'appt_type': forms.Select(choices=Appointment.APPT_TYPE_CHOICES, attrs={
                'class': 'form-select'
            }),
            'appt_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'appt_time': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-select'
            }),
            'product_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'carrier': forms.Select(attrs={
                'class': 'form-select'
            }),
            'bol_shipment_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter BOL or Shipment Number'
            }),
            'delivery_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Delivery Number'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.filter(active=True)
        self.fields['carrier'].queryset = Carrier.objects.filter(active=True)
        self.fields['product_type'].queryset = ProductType.objects.filter(active=True)


class AppointmentFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    appt_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('IB', 'Inbound'), ('OB', 'Outbound')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('Scheduled', 'Scheduled'),
            ('Checked In', 'Checked In'),
            ('Completed', 'Completed'),
            ('Early', 'Early'),
            ('On Time', 'On Time'),
            ('Late', 'Late'),
            ('Missed', 'Missed'),
            ('Cancelled', 'Cancelled'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    carrier = forms.ModelChoiceField(
        required=False,
        queryset=Carrier.objects.filter(active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    customer = forms.ModelChoiceField(
        required=False,
        queryset=Customer.objects.filter(active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search BOL, carrier, customer, driver, trailer...'
        })
    )


class CheckInForm(forms.ModelForm):
    class Meta:
        model = DriverVisit
        fields = [
            'visitor_name', 'trailer_no', 'drivers_license_state',
            'load_lock', 'assigned_door', 'pit_operator', 'notes'
        ]
        widgets = {
            'visitor_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Driver / Visitor Name'
            }),
            'trailer_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Trailer Number'
            }),
            'drivers_license_state': forms.Select(attrs={
                'class': 'form-select'
            }),
            'load_lock': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_door': forms.Select(attrs={
                'class': 'form-select'
            }),
            'pit_operator': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Check-in notes...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_door'].queryset = Door.objects.filter(active=True)
        self.fields['pit_operator'].queryset = PITOperator.objects.filter(active=True)
        self.fields['drivers_license_state'].choices = [('', '-- Select State --')] + [
            (s, s) for s in US_STATES
        ]


class CheckOutForm(forms.ModelForm):
    check_out_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )

    class Meta:
        model = DriverVisit
        fields = ['check_out_time', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Final notes...'
            }),
        }


class KPIExportForm(forms.Form):
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date'
        })
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date'
        })
    )
    appt_type = forms.ChoiceField(
        choices=[('All', 'All'), ('IB', 'Inbound'), ('OB', 'Outbound')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[
            ('All', 'All'),
            ('Early', 'Early'),
            ('On Time', 'On Time'),
            ('Late', 'Late'),
            ('Missed', 'Missed'),
            ('Cancelled', 'Cancelled'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    include_scheduled = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_checked_in = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    include_completed = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC'
]
