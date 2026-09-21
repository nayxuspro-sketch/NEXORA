import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract model providing automatic timestamp tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(TimeStampedModel):
    """
    Abstract model enforcing multi-tenancy by linking every business record
    to a specific Company.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
        db_index=True
    )

    class Meta:
        abstract = True
