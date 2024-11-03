from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_staff_permissions(sender, instance, created, **kwargs):
    # Check will get called on every save so we also need to avoid recursion
    if instance.is_staff and not getattr(instance, '_skip_permissions', False):
        instance._skip_permissions = True

        # Get the content type for the user model
        content_type = ContentType.objects.get_for_model(User)
        
        # Define the required permissions
        required_permissions = Permission.objects.filter(content_type=content_type, codename__in=[
            'view_user',
            'change_user',
        ])
        
        # Assign permissions to the user
        for permission in required_permissions:
            if not instance.user_permissions.filter(id=permission.id).exists():
                instance.user_permissions.add(permission)
        
        instance.save()
