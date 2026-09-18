from apps.accounts.repositories import UserRepository
from apps.bookings.repositories import BookingRepository
from apps.events.repositories import EventRepository
from apps.events.repositories import VendorRepository



class DashboardService:
    """
    Provides aggregated read-only data for the staff dashboard.

    Dashboard-specific aggregation belongs here.
    Domain database operations remain inside repositories.
    """

    @staticmethod
    def get_overview():
        """
        Return the main overview statistics for the dashboard.
        """

        return {
            "customers": {
                "total": UserRepository.count_customers(),
            },
            "vendors": {
                "total": VendorRepository.count(),
                "active": VendorRepository.count_active(),
            },
            "events": {
                "total": EventRepository.count(),
                "active": EventRepository.count_active(),
            },
            "bookings": {
                "total": BookingRepository.count(),
                "confirmed": BookingRepository.count_confirmed(),
            },
        }

    @staticmethod
    def get_upcoming_events():
        """
        Return upcoming events for dashboard display.
        """

        return EventRepository.get_upcoming()

    @staticmethod
    def get_recent_bookings(limit: int = 10):
        """
        Return recent bookings for dashboard display.
        """

        return BookingRepository.get_recent(
            limit=limit,
        )