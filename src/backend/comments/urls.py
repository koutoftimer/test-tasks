from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"comments", views.CommentViewSet, basename="comment")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/", include("accounts.urls")),
    path("api/", include("attachments.urls")),
    path("api/sanitize/", views.sanitize, name="sanitize"),
    path("api/captcha/", views.captcha, name="captcha"),
    path("captcha/", include("captcha.urls")),
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.jwt")),
]

if settings.DEBUG:
    urlpatterns += [
        path("silk/", include("silk.urls", namespace="silk")),
    ]
