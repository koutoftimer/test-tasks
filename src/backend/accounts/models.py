from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_lifecycle import LifecycleModel, hook, BEFORE_CREATE, BEFORE_UPDATE

from comments.models import avatar_file_path, resize_image


class Profile(LifecycleModel):
    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name="profile"
    )
    homepage = models.URLField(max_length=200, blank=True, null=True)
    avatar = models.ImageField(upload_to=avatar_file_path, blank=True, null=True)

    class Meta:
        app_label = "comments"
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    @hook(BEFORE_CREATE)
    @hook(BEFORE_UPDATE, when="avatar", has_changed=True)
    def resize_avatar(self):
        """Makes sure that avatar get scaled to appropriate size"""
        if self.avatar:
            self.avatar = resize_image(self.avatar, *settings.MAX_AVATAR_SIZE)

    def __str__(self):
        return f"Profile #{self.pk} for {self.user.username}"


@receiver(post_save, sender=get_user_model())
def create_profile_for_user(sender, instance, created, **kwargs):
    """Create Profile for new users (during registration)."""
    if created:
        Profile.objects.get_or_create(user=instance)
