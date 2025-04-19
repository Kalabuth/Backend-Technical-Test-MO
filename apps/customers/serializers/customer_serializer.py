from rest_framework import serializers

from apps.customers.models.customers import Customer


class CustomerSerializer(serializers.ModelSerializer):
    """
    Create / Retrieve Customer.
    On creation, status is forced to ACTIVE (1).
    """

    class Meta:
        model = Customer
        fields = ["external_id", "status", "score", "preapproved_at"]
        read_only_fields = ["status", "preapproved_at"]

    def create(self, validated_data):
        validated_data["status"] = 1
        return super().create(validated_data)


class CustomerUploadSerializer(serializers.Serializer):
    """
    Validate a plain‑text upload of many customers.
    Expects one FileField with lines: external_id,score
    """

    file = serializers.FileField()


class CustomerBalanceSerializer(serializers.Serializer):
    """
    Output for the balance endpoint.
    - external_id
    - score
    - total_debt (sum of all loans with status pending/active)
    - available_amount (score minus total_debt)
    """

    external_id = serializers.CharField()
    score = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_debt = serializers.DecimalField(max_digits=12, decimal_places=2)
    available_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
