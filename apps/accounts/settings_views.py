from rest_framework import serializers, viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import Group, Permission
from apps.accounts.models import User, UserRole
from apps.companies.models import Company


class PermissionSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source='content_type.app_label', read_only=True)

    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'app_label']


class GroupSerializer(serializers.ModelSerializer):
    permissions_details = PermissionSerializer(source='permissions', many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
        source='permissions',
        required=False
    )
    users_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions_details', 'permission_ids', 'users_count']

    def get_users_count(self, obj):
        return obj.user_set.count()


class GroupViewSet(viewsets.ModelViewSet):
    """
    CRUD management of user groups/profiles and their assigned permissions.
    """
    permission_classes = [AllowAny]
    queryset = Group.objects.prefetch_related('permissions').all().order_by('name')
    serializer_class = GroupSerializer


class SystemPermissionsListView(APIView):
    """
    Returns all system permissions grouped by domain for easy UI toggles.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        relevant_apps = ['accounts', 'sales', 'inventory', 'purchases', 'pos', 'audit', 'companies', 'ai_assistant']
        perms = Permission.objects.filter(content_type__app_label__in=relevant_apps).select_related('content_type').order_by('content_type__app_label', 'name')
        
        grouped = {}
        for p in perms:
            app = p.content_type.app_label
            if app not in grouped:
                grouped[app] = []
            grouped[app].append({
                'id': p.id,
                'name': p.name,
                'codename': p.codename,
            })
            
        return Response({
            'status': 'success',
            'permissions_by_module': grouped,
            'total_count': perms.count()
        })


class UserManagementSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        write_only=True,
        source='groups',
        required=False
    )
    groups_details = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'phone', 'company', 'company_name', 'is_active', 'date_joined',
            'group_ids', 'groups_details', 'password'
        ]
        read_only_fields = ['id', 'date_joined']

    def get_groups_details(self, obj):
        return [{'id': g.id, 'name': g.name} for g in obj.groups.all()]

    def create(self, validated_data):
        groups = validated_data.pop('groups', [])
        password = validated_data.pop('password', 'Pass123456!')
        if not validated_data.get('company'):
            validated_data['company'] = Company.objects.first()

        user = User.objects.create_user(password=password, **validated_data)
        if groups:
            user.groups.set(groups)
        return user

    def update(self, obj, validated_data):
        groups = validated_data.pop('groups', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(obj, attr, value)
        if password:
            obj.set_password(password)
        obj.save()
        if groups is not None:
            obj.groups.set(groups)
        return obj


class UserManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related('groups').all().order_by('-date_joined')
    serializer_class = UserManagementSerializer

    def get_permissions(self):
        return [AllowAny()]

    def perform_create(self, serializer):
        user = self.request.user
        if user and user.is_authenticated:
            if user.role != UserRole.ADMIN and not user.is_superuser:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Seul un administrateur d'entreprise peut créer un utilisateur.")
            serializer.save(company_id=user.company_id)
        else:
            serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if user and user.is_authenticated:
            target_user = self.get_object()
            if user.role != UserRole.ADMIN and not user.is_superuser:
                if target_user.id != user.id:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Vous ne pouvez pas modifier un autre utilisateur.")
                if 'role' in serializer.validated_data and serializer.validated_data['role'] != user.role:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Vous n'êtes pas autorisé à modifier vos propres permissions ou votre rôle.")
        serializer.save()
