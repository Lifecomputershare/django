from django.utils import timezone
from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company, SubscriptionPlan, CompanySubscription, Job, Application, AIMatchLog
from .serializers import (
    CompanySerializer,
    SubscriptionPlanSerializer,
    CompanySubscriptionSerializer,
    JobSerializer,
    ApplicationSerializer,
    AIMatchLogSerializer,
)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]


class CompanySubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, "profile", None)
        if profile is None or profile.company is None:
            return Response(
                {"detail": "User is not linked to a company"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription = (
            CompanySubscription.objects.filter(company=profile.company, is_active=True)
            .order_by("-end_date")
            .first()
        )
        if subscription is None:
            return Response(
                {"detail": "No active subscription found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CompanySubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = getattr(request.user, "profile", None)
        if profile is None or profile.company is None:
            return Response(
                {"detail": "User is not linked to a company"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        plan_id = request.data.get("plan_id")
        if not plan_id:
            return Response(
                {"detail": "plan_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"detail": "Invalid plan_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=plan.duration_days)
        subscription = CompanySubscription.objects.create(
            company=profile.company,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
        )
        serializer = CompanySubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AIMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            return Response(
                {"detail": "Application not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ApplicationSerializer(application)
        latest_log = (
            AIMatchLog.objects.filter(application=application)
            .order_by("-processed_at")
            .first()
        )
        log_serializer = AIMatchLogSerializer(latest_log) if latest_log else None
        data = {
            "application": serializer.data,
            "latest_match_log": log_serializer.data if log_serializer else None,
        }
        return Response(data, status=status.HTTP_200_OK)


class StripePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response(
            {"detail": "Stripe payment endpoint stub"},
            status=status.HTTP_200_OK,
        )


class KhaltiPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response(
            {"detail": "Khalti payment endpoint stub"},
            status=status.HTTP_200_OK,
        )
