from django.urls import path

from apps.admin.moderation.views import (
    AdminChannelsView,
    ModerationRequestListView,
)

app_name = "admin_moderation"

urlpatterns = [
    path("", ModerationRequestListView.as_view(), name="list"),
    path(
        "channels/",
        AdminChannelsView.as_view(),
        name="channels",
    ),
]