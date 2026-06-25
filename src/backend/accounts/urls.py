from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"profile", views.ProfileViewSet, basename="profile")

urlpatterns = [
    path("", include(router.urls)),
]
