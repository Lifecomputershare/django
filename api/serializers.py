from rest_framework import serializers
from .models import Company, SubscriptionPlan, CompanySubscription, Job, Application, AIMatchLog


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"


class CompanySubscriptionSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = CompanySubscription
        fields = "__all__"


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = "__all__"


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = "__all__"


class AIMatchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMatchLog
        fields = "__all__"

