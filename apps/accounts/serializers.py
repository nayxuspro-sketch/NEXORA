from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, UserRole


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['company_id'] = str(user.company_id) if user.company_id else None
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        perms = list(self.user.get_all_permissions())
        groups = list(self.user.groups.values_list('name', flat=True))
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'company_id': str(self.user.company_id) if self.user.company_id else None,
            'company_name': self.user.company.name if self.user.company else None,
            'is_superuser': self.user.is_superuser,
            'groups': groups,
            'permissions': perms,
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    permissions = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'phone', 'company', 'company_name', 'is_active', 'is_superuser',
            'groups', 'permissions', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'permissions', 'groups']
        extra_kwargs = {
            'company': {'required': False}
        }

    def get_permissions(self, obj):
        return list(obj.get_all_permissions())

    def get_groups(self, obj):
        return list(obj.groups.values_list('name', flat=True))


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'first_name', 'last_name',
            'role', 'phone', 'is_active'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user
