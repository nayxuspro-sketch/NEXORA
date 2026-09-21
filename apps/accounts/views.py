from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, UserRole
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    CustomTokenObtainPairSerializer
)
from apps.common.permissions import IsAuthenticatedAndInTenant


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedAndInTenant]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['email', 'first_name', 'date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        if user.is_superuser and not user.company_id:
            return User.objects.all()
        return User.objects.filter(company_id=user.company_id)

    def perform_create(self, serializer):
        user = self.request.user
        # Strict RBAC: only ADMIN can create new users in the company
        if user.role != UserRole.ADMIN and not user.is_superuser:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul un administrateur d'entreprise peut créer un utilisateur.")
        serializer.save(company_id=user.company_id)

    def perform_update(self, serializer):
        user = self.request.user
        target_user = self.get_object()
        # Non-admin cannot elevate roles or modify other users
        if user.role != UserRole.ADMIN and not user.is_superuser:
            if target_user.id != user.id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Vous ne pouvez pas modifier un autre utilisateur.")
            if 'role' in serializer.validated_data and serializer.validated_data['role'] != user.role:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Vous n'êtes pas autorisé à modifier vos propres permissions ou votre rôle.")
        serializer.save()

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
