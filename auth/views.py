from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.authentication import generate_access_token, generate_refresh_token, decode_token
from api.models import UserProfile, Company


@api_view(["POST"])
@permission_classes([AllowAny])
def registerUser(request):
    email = request.data.get("email")
    password = request.data.get("password")
    role = request.data.get("role")
    company_id = request.data.get("company_id")
    if not email or not password or not role:
        return Response(
            {"detail": "email, password and role are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if User.objects.filter(email__iexact=email).exists():
        return Response(
            {"detail": "Email already in use"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if role not in dict(UserProfile.ROLE_CHOICES):
        return Response(
            {"detail": "Invalid role"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user = User(username=email, email=email, is_active=True)
    user.set_password(password)
    user.save()
    company = None
    if company_id:
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                {"detail": "Invalid company_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    profile = UserProfile.objects.create(
        user=user,
        email=email,
        role=role,
        company=company,
    )
    access = generate_access_token(user)
    refresh = generate_refresh_token(user)
    return Response(
        {
            "access": access,
            "refresh": refresh,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": profile.role,
                "company_id": profile.company_id,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def loginUser(request):
    email = request.data.get("email")
    password = request.data.get("password")
    if not email or not password:
        return Response(
            {"detail": "email and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not user.check_password(password):
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not user.is_active:
        return Response(
            {"detail": "User is inactive"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    profile = getattr(user, "profile", None)
    access = generate_access_token(user)
    refresh = generate_refresh_token(user)
    return Response(
        {
            "access": access,
            "refresh": refresh,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": profile.role if profile else None,
                "company_id": profile.company_id if profile else None,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def refreshToken(request):
    refresh = request.data.get("refresh")
    if not refresh:
        return Response(
            {"detail": "refresh token is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    payload = decode_token(refresh, "refresh")
    user_id = payload.get("user_id")
    if not user_id:
        return Response(
            {"detail": "Invalid token payload"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return Response(
            {"detail": "User not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    profile = getattr(user, "profile", None)
    access = generate_access_token(user)
    new_refresh = generate_refresh_token(user)
    return Response(
        {
            "access": access,
            "refresh": new_refresh,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": profile.role if profile else None,
                "company_id": profile.company_id if profile else None,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logoutUser(request):
    return Response(status=status.HTTP_204_NO_CONTENT)
