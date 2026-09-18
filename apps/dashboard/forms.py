from django import forms

from apps.accounts.models import User
from apps.events.models import Event, Vendor

class DashboardCustomerUpdateForm(forms.ModelForm):
    """
    Form used by staff to update customer profile information.
    """

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
        ]

        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "customer@example.com",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "First name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Last name",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        existing_user = (
            User.objects
            .filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .first()
        )

        if existing_user:
            raise forms.ValidationError(
                "A user with this email already exists."
            )

        return email




class DashboardVendorForm(forms.ModelForm):
    """
    Staff dashboard form for creating and updating vendors.
    """

    class Meta:
        model = Vendor

        fields = [
            "name",
            "email",
            "phone",
            "address",
            "description",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Vendor name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "vendor@example.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Vendor address",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Vendor description",
                }
            ),
        }





class DashboardEventForm(forms.ModelForm):
    """
    Staff dashboard form for creating and updating events.
    """

    class Meta:
        model = Event

        fields = [
            "vendor",
            "title",
            "description",
            "venue_name",
            "address",
            "latitude",
            "longitude",
            "start_datetime",
            "end_datetime",
            "total_seats",
            "ticket_price",
        ]

        widgets = {
            "vendor": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Event title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Event description",
                }
            ),
            "venue_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Venue name",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Event address",
                }
            ),
            "latitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "any",
                    "placeholder": "e.g. 11.2588",
                }
            ),
            "longitude": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "any",
                    "placeholder": "e.g. 75.7804",
                }
            ),
            "start_datetime": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "end_datetime": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "total_seats": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "placeholder": "Total seats",
                }
            ),
            "ticket_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "Ticket price",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only active vendors can receive new events.
        self.fields["vendor"].queryset = (
            Vendor.objects
            .filter(is_active=True)
            .order_by("name")
        )