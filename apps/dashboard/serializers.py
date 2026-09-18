from rest_framework import serializers


class DashboardCustomerStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField(read_only=True)


class DashboardVendorStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField(read_only=True)
    active = serializers.IntegerField(read_only=True)


class DashboardEventStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField(read_only=True)
    active = serializers.IntegerField(read_only=True)


class DashboardBookingStatsSerializer(serializers.Serializer):
    total = serializers.IntegerField(read_only=True)
    confirmed = serializers.IntegerField(read_only=True)


class DashboardOverviewSerializer(serializers.Serializer):
    customers = DashboardCustomerStatsSerializer(read_only=True)
    vendors = DashboardVendorStatsSerializer(read_only=True)
    events = DashboardEventStatsSerializer(read_only=True)
    bookings = DashboardBookingStatsSerializer(read_only=True)