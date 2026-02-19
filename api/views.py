from django.utils import timezone
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView

from SmartHire.responses import api_success, api_error
from .models import Company, SubscriptionPlan, CompanySubscription, Job, Application, AIMatchLog, UserProfile
from .permissions import IsAdminOrRecruiter
from .serializers import (
    CompanySerializer,
    SubscriptionPlanSerializer,
    CompanySubscriptionSerializer,
    JobSerializer,
    ApplicationSerializer,
    AIMatchLogSerializer,
)


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrRecruiter]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Company.objects.none()
        profile = getattr(user, "profile", None)
        if not profile:
            return Company.objects.none()
        if profile.role == UserProfile.ROLE_ADMIN:
            return Company.objects.all()
        if profile.company_id:
            return Company.objects.filter(id=profile.company_id)
        return Company.objects.none()

    def perform_create(self, serializer):
        instance = serializer.save()
        user = self.request.user
        profile = getattr(user, "profile", None)
        if profile and not profile.company:
            profile.company = instance
            profile.save(update_fields=["company"])


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrRecruiter]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Job.objects.none()
        profile = getattr(user, "profile", None)
        if not profile:
            return Job.objects.filter(is_active=True)
        if profile.role == UserProfile.ROLE_ADMIN:
            return Job.objects.all()
        if profile.role == UserProfile.ROLE_RECRUITER and profile.company_id:
            return Job.objects.filter(company_id=profile.company_id)
        if profile.role == UserProfile.ROLE_CANDIDATE:
            return Job.objects.filter(is_active=True)
        return Job.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        profile = getattr(user, "profile", None)
        if profile and profile.company:
            serializer.save(company=profile.company)
        else:
            serializer.save()


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Application.objects.none()
        profile = getattr(user, "profile", None)
        if profile and profile.role == UserProfile.ROLE_ADMIN:
            return Application.objects.all()
        if profile and profile.role == UserProfile.ROLE_RECRUITER and profile.company_id:
            return Application.objects.filter(job__company_id=profile.company_id)
        return Application.objects.filter(applicant=user)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(applicant=user)


class CompanySubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, "profile", None)
        if profile is None or profile.company is None:
            return api_error(
                {"detail": "User is not linked to a company"},
                status.HTTP_400_BAD_REQUEST,
            )
        subscription = (
            CompanySubscription.objects.filter(company=profile.company, is_active=True)
            .order_by("-end_date")
            .first()
        )
        if subscription is None:
            return api_error(
                {"detail": "No active subscription found"},
                status.HTTP_404_NOT_FOUND,
            )
        serializer = CompanySubscriptionSerializer(subscription)
        return api_success(serializer.data, status_code=status.HTTP_200_OK)


class SubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = getattr(request.user, "profile", None)
        if profile is None or profile.company is None:
            return api_error(
                {"detail": "User is not linked to a company"},
                status.HTTP_400_BAD_REQUEST,
            )
        plan_id = request.data.get("plan_id")
        if not plan_id:
            return api_error(
                {"detail": "plan_id is required"},
                status.HTTP_400_BAD_REQUEST,
            )
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return api_error(
                {"detail": "Invalid plan_id"},
                status.HTTP_400_BAD_REQUEST,
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
        return api_success(serializer.data, status_code=status.HTTP_201_CREATED)


class AIMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            return api_error(
                {"detail": "Application not found"},
                status.HTTP_404_NOT_FOUND,
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
        return api_success(data, status_code=status.HTTP_200_OK)


class StripePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return api_success(
            {"detail": "Stripe payment endpoint stub"},
            status_code=status.HTTP_200_OK,
        )


class KhaltiPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return api_success(
            {"detail": "Khalti payment endpoint stub"},
            status_code=status.HTTP_200_OK,
        )
