
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(r"companies", views.CompanyViewSet, basename="company")
router.register(r"jobs", views.JobViewSet, basename="job")
router.register(r"applications", views.ApplicationViewSet, basename="application")
router.register(r"subscriptions/plans", views.SubscriptionPlanViewSet, basename="subscription-plan")


urlpatterns = [
    path("subscriptions/company", views.CompanySubscriptionView.as_view(), name="company-subscription"),
    path("subscriptions/subscribe", views.SubscribeView.as_view(), name="subscribe-plan"),
    path("ai/match/<int:pk>/", views.AIMatchView.as_view(), name="ai-match"),
    path("payments/stripe", views.StripePaymentView.as_view(), name="stripe-payment"),
    path("payments/khalti", views.KhaltiPaymentView.as_view(), name="khalti-payment"),
    path("", include(router.urls)),
]
