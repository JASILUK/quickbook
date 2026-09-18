from rest_framework import status

from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.accounts.permissions import IsStaffUser
from apps.dashboard.serializers import DashboardOverviewSerializer
from apps.dashboard.services import DashboardService

from apps.accounts.base_views import BaseAPIView
from apps.accounts.schemas import response_schema


@extend_schema(
    summary="Get dashboard overview",
    description=(
        "Return aggregated statistics for the staff dashboard. "
        "Staff access required."
    ),
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=response_schema(
                data_serializer=DashboardOverviewSerializer,
            ),
            description="Dashboard overview retrieved successfully.",
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            description="Authentication required.",
        ),
        status.HTTP_403_FORBIDDEN: OpenApiResponse(
            description="Staff access required.",
        ),
    },
)
class DashboardView(BaseAPIView):
    """
    Staff-only dashboard overview API.
    """

    permission_classes = [IsStaffUser]

    def get(self, request):
        dashboard_data = DashboardService.get_overview()

        serializer = DashboardOverviewSerializer(
            dashboard_data,
        )

        return self.success_response(
            data=serializer.data,
            message="Dashboard overview retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )





#======================================




from django.views.generic import TemplateView

from apps.dashboard.mixins import StaffDashboardRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.accounts.services.customer_service import CustomerService
from apps.events.services.vendor_service import VendorService
from apps.events.services.event_service import EventService
from apps.dashboard.forms import DashboardCustomerUpdateForm, DashboardVendorForm, DashboardEventForm
from apps.dashboard.mixins import StaffDashboardRequiredMixin
from apps.referrals.services import ReferralService
from config.exceptions import ReferralServiceError
from apps.bookings.services import BookingService
from apps.events.repositories import EventRepository

class DashboardHomeView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff dashboard home page.
    """

    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["overview"] = DashboardService.get_overview()
        context["upcoming_events"] = (
            DashboardService.get_upcoming_events()
        )
        context["recent_bookings"] = (
            DashboardService.get_recent_bookings()
        )

        return context
    


class DashboardCustomerListView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff customer management list.
    """

    template_name = "dashboard/customers/list.html"

    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search = self.request.GET.get(
            "search",
            "",
        ).strip()

        customers = CustomerService.list_customers()

        if search:
            from django.db.models import Q

            customers = customers.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        paginator = Paginator(
            customers,
            self.paginate_by,
        )

        page_number = self.request.GET.get("page")

        page_obj = paginator.get_page(
            page_number
        )

        context["customers"] = page_obj
        context["page_obj"] = page_obj
        context["search"] = search

        return context


class DashboardCustomerDetailView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    template_name = "dashboard/customers/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        customer_id = kwargs["customer_id"]

        # ---------------------------------------------------------
        # Customer
        # ---------------------------------------------------------

        customer = CustomerService.get_customer(
            user_id=customer_id,
        )

        context["customer"] = customer

        # ---------------------------------------------------------
        # Referral information
        # ---------------------------------------------------------

        try:
            context["referral_stats"] = ReferralService.get_stats(
                user_id=customer.id,
            )

            context["referral_root"] = ReferralService.get_root(
                user_id=customer.id,
            )

            context["referral_tree"] = ReferralService.get_tree(
                user_id=customer.id,
            )

            context["has_referral_node"] = True

        except ReferralServiceError:
            context["referral_stats"] = None
            context["referral_root"] = None
            context["referral_tree"] = None
            context["has_referral_node"] = False

        return context


class DashboardCustomerUpdateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff customer update page.
    """

    template_name = "dashboard/customers/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        customer = CustomerService.get_customer(
            user_id=kwargs["user_id"],
        )

        context["customer"] = customer
        context["form"] = DashboardCustomerUpdateForm(
            instance=customer,
        )

        return context

    def post(self, request, *args, **kwargs):
        customer = CustomerService.get_customer(
            user_id=kwargs["user_id"],
        )

        form = DashboardCustomerUpdateForm(
            request.POST,
            instance=customer,
        )

        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(
                    **kwargs,
                    form=form,
                )
            )

        CustomerService.update_customer(
            user_id=customer.id,
            **form.cleaned_data,
        )

        messages.success(
            request,
            "Customer updated successfully.",
        )

        return redirect(
            "dashboard:customer-detail",
            user_id=customer.id,
        )


class DashboardCustomerActivateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff customer activation action.
    """

    def post(self, request, *args, **kwargs):
        CustomerService.activate_customer(
            user_id=kwargs["user_id"],
        )

        messages.success(
            request,
            "Customer activated successfully.",
        )

        return redirect(
            "dashboard:customer-detail",
            user_id=kwargs["user_id"],
        )


class DashboardCustomerDeactivateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff customer deactivation action.
    """

    def post(self, request, *args, **kwargs):
        CustomerService.deactivate_customer(
            user_id=kwargs["user_id"],
        )

        messages.success(
            request,
            "Customer deactivated successfully.",
        )

        return redirect(
            "dashboard:customer-detail",
            user_id=kwargs["user_id"],
        )


class DashboardVendorListView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff vendor management list.
    """

    template_name = "dashboard/vendors/list.html"

    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search = self.request.GET.get(
            "search",
            "",
        ).strip()

        vendors = VendorService.search_vendors(
            search=search,
        )

        paginator = Paginator(
            vendors,
            self.paginate_by,
        )

        page_number = self.request.GET.get("page")

        page_obj = paginator.get_page(
            page_number,
        )

        context["vendors"] = page_obj
        context["page_obj"] = page_obj
        context["search"] = search

        return context


class DashboardVendorCreateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff vendor creation page.
    """

    template_name = "dashboard/vendors/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["form"] = DashboardVendorForm()

        context["page_title"] = "Add Vendor"

        return context

    def post(self, request, *args, **kwargs):
        form = DashboardVendorForm(
            request.POST,
        )

        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(
                    **kwargs,
                    form=form,
                )
            )

        vendor = VendorService.create_vendor(
            created_by=request.user,
            **form.cleaned_data,
        )

        messages.success(
            request,
            "Vendor created successfully.",
        )

        return redirect(
            "dashboard:vendor-detail",
            vendor_id=vendor.id,
        )


class DashboardVendorDetailView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff vendor detail page.
    """

    template_name = "dashboard/vendors/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        vendor = VendorService.get_vendor(
            vendor_id=kwargs["vendor_id"],
        )

        context["vendor"] = vendor

        return context


class DashboardVendorUpdateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff vendor update page.
    """

    template_name = "dashboard/vendors/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        vendor = VendorService.get_vendor(
            vendor_id=kwargs["vendor_id"],
        )

        context["vendor"] = vendor
        context["form"] = DashboardVendorForm(
            instance=vendor,
        )
        context["page_title"] = "Edit Vendor"

        return context

    def post(self, request, *args, **kwargs):
        vendor = VendorService.get_vendor(
            vendor_id=kwargs["vendor_id"],
        )

        form = DashboardVendorForm(
            request.POST,
            instance=vendor,
        )

        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(
                    **kwargs,
                    form=form,
                )
            )

        VendorService.update_vendor(
            vendor_id=vendor.id,
            **form.cleaned_data,
        )

        messages.success(
            request,
            "Vendor updated successfully.",
        )

        return redirect(
            "dashboard:vendor-detail",
            vendor_id=vendor.id,
        )


class DashboardVendorActivateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff vendor activation action.
    """

    def post(self, request, *args, **kwargs):
        VendorService.activate_vendor(
            vendor_id=kwargs["vendor_id"],
        )

        messages.success(
            request,
            "Vendor activated successfully.",
        )

        return redirect(
            "dashboard:vendor-detail",
            vendor_id=kwargs["vendor_id"],
        )


class DashboardVendorDeactivateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff vendor deactivation action.
    """

    def post(self, request, *args, **kwargs):
        VendorService.deactivate_vendor(
            vendor_id=kwargs["vendor_id"],
        )

        messages.success(
            request,
            "Vendor deactivated successfully.",
        )

        return redirect(
            "dashboard:vendor-detail",
            vendor_id=kwargs["vendor_id"],
        )

class DashboardEventListView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff event management list.
    """

    template_name = "dashboard/events/list.html"

    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search = self.request.GET.get(
            "search",
            "",
        ).strip()

        vendor_id = self.request.GET.get(
            "vendor_id",
            "",
        ).strip()

        events = EventService.list_staff_events(
            staff_user=self.request.user,
            search=search or None,
            vendor_id=int(vendor_id) if vendor_id.isdigit() else None,
        )

        paginator = Paginator(
            events,
            self.paginate_by,
        )

        page_number = self.request.GET.get("page")

        page_obj = paginator.get_page(
            page_number,
        )

        context["events"] = page_obj
        context["page_obj"] = page_obj
        context["search"] = search
        context["selected_vendor_id"] = vendor_id

        # Used by the filter dropdown.
        from apps.events.repositories import VendorRepository

        context["vendors"] = VendorRepository.get_active()

        return context


class DashboardEventCreateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff event creation page.
    """

    template_name = "dashboard/events/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["form"] = DashboardEventForm()
        context["page_title"] = "Add Event"

        return context

    def post(self, request, *args, **kwargs):
        form = DashboardEventForm(
            request.POST,
        )

        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(
                    **kwargs,
                    form=form,
                )
            )

        data = form.cleaned_data

        event = EventService.create_event(
            staff_user=request.user,
            vendor_id=data["vendor"].id,
            title=data["title"],
            description=data["description"],
            venue_name=data["venue_name"],
            address=data["address"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            start_datetime=data["start_datetime"],
            end_datetime=data["end_datetime"],
            total_seats=data["total_seats"],
            ticket_price=data["ticket_price"],
        )

        messages.success(
            request,
            "Event created successfully.",
        )

        return redirect(
            "dashboard:event-detail",
            event_id=event.id,
        )


class DashboardEventDetailView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff event detail page.
    """

    template_name = "dashboard/events/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event = EventService.get_event(
            event_id=kwargs["event_id"],
            staff_user=self.request.user,
        )

        context["event"] = event

        return context


class DashboardEventUpdateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff event update page.
    """

    template_name = "dashboard/events/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event = EventService.get_event(
            event_id=kwargs["event_id"],
            staff_user=self.request.user,
        )

        context["event"] = event
        context["form"] = DashboardEventForm(
            instance=event,
        )
        context["page_title"] = "Edit Event"

        return context

    def post(self, request, *args, **kwargs):
        event = EventService.get_event(
            event_id=kwargs["event_id"],
            staff_user=request.user,
        )

        form = DashboardEventForm(
            request.POST,
            instance=event,
        )

        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(
                    **kwargs,
                    form=form,
                )
            )

        data = form.cleaned_data

        EventService.update_event(
            staff_user=request.user,
            event_id=event.id,
            vendor_id=data["vendor"].id,
            title=data["title"],
            description=data["description"],
            venue_name=data["venue_name"],
            address=data["address"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            start_datetime=data["start_datetime"],
            end_datetime=data["end_datetime"],
            total_seats=data["total_seats"],
            ticket_price=data["ticket_price"],
        )

        messages.success(
            request,
            "Event updated successfully.",
        )

        return redirect(
            "dashboard:event-detail",
            event_id=event.id,
        )


class DashboardEventActivateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff event activation action.
    """

    def post(self, request, *args, **kwargs):
        EventService.activate_event(
            staff_user=request.user,
            event_id=kwargs["event_id"],
        )

        messages.success(
            request,
            "Event activated successfully.",
        )

        return redirect(
            "dashboard:event-detail",
            event_id=kwargs["event_id"],
        )


class DashboardEventDeactivateView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    """
    Staff event deactivation action.
    """

    def post(self, request, *args, **kwargs):
        EventService.deactivate_event(
            staff_user=request.user,
            event_id=kwargs["event_id"],
        )

        messages.success(
            request,
            "Event deactivated successfully.",
        )

        return redirect(
            "dashboard:event-detail",
            event_id=kwargs["event_id"],
        )



class DashboardBookingListView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    template_name = "dashboard/bookings/list.html"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search = self.request.GET.get("search", "").strip()
        status_filter = self.request.GET.get("status", "").strip()
        event_id = self.request.GET.get("event_id", "").strip()

        bookings = BookingService.list_bookings(
            user=self.request.user,
            event_id=int(event_id) if event_id.isdigit() else None,
            booking_status=status_filter or None,
            search=search or None,
        )

        paginator = Paginator(
            bookings,
            self.paginate_by,
        )

        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["bookings"] = page_obj
        context["page_obj"] = page_obj

        context["search"] = search
        context["selected_status"] = status_filter
        context["selected_event_id"] = event_id

        context["events"] = EventRepository.get_all()

        return context


class DashboardBookingDetailView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    template_name = "dashboard/bookings/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        booking = BookingService.get_booking(
            booking_id=kwargs["booking_id"],
            user=self.request.user,
        )

        context["booking"] = booking

        return context


class DashboardBookingCancelView(
    StaffDashboardRequiredMixin,
    TemplateView,
):
    def post(self, request, *args, **kwargs):

        booking_id = kwargs["booking_id"]

        BookingService.cancel_booking(
            booking_id=booking_id,
            user=request.user,
        )

        messages.success(
            request,
            "Booking cancelled successfully.",
        )

        return redirect(
            "dashboard:booking-detail",
            booking_id=booking_id,
        )