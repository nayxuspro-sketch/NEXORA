from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrateur Entreprise'
    MANAGER = 'MANAGER', 'Responsable de Magasin'
    CASHIER = 'CASHIER', 'Caissier / Vendeur'
    STOCK_KEEPER = 'STOCK_KEEPER', 'Gestionnaire de Stock'
    ACCOUNTANT = 'ACCOUNTANT', 'Comptable'
    AUDITOR = 'AUDITOR', 'Auditeur'


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField('Email', unique=True, db_index=True)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CASHIER
    )
    phone = models.CharField(max_length=30, blank=True, default='')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['email']

    def __str__(self):
        return f"{self.email} ({self.role})"
