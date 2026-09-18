from rest_framework.response import Response
from rest_framework.views import APIView

from config.pagination import StandardPagination


class BaseAPIView(APIView):
    """
    Base API view for common successful responses
    and standard pagination.
    """

    pagination_class = StandardPagination

    def success_response(
        self,
        *,
        data=None,
        message=None,
        status_code=200,
    ):
        response_data = {
            "success": True,
        }

        if message is not None:
            response_data["message"] = message

        if data is not None:
            response_data["data"] = data

        return Response(
            response_data,
            status=status_code,
        )

    def paginate_queryset(self, queryset):
        """
        Paginate a queryset using the standard QuickBook paginator.
        """
        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            queryset,
            self.request,
            view=self,
        )

        return paginator, page

    def paginated_success_response(
        self,
        *,
        paginator,
        data,
        message=None,
        status_code=200,
    ):
        """
        Return a paginated response while preserving
        the common QuickBook response structure.
        """

        pagination_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": data,
        }

        return self.success_response(
            data=pagination_data,
            message=message,
            status_code=status_code,
        )