from django.test import TestCase
from django.urls import reverse

from apps.admin.moderation.models import ModerationRequest
from apps.parser.models import TelegramChannel
from apps.users.models import User


class AdminChannelsViewTests(TestCase):
    def setUp(self) -> None:
        self.admin = User.objects.create_user(
            username="channels-view-admin",
            email="channels-view-admin@example.com",
            password="password",
            role="admin",
        )
        self.url = reverse("admin_channels")

    def test_view_requires_admin(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_view_returns_approved_channels_and_categories(self) -> None:
        self.client.force_login(self.admin)

        approved_channel = TelegramChannel.objects.create(
            channel_id=2001,
            username="approved_for_admin",
            title="Approved for admin",
            participants_count=1250,
            category="Технологии",
            is_verified=True,
        )
        pending_channel = TelegramChannel.objects.create(
            channel_id=2002,
            username="pending_for_admin",
            title="Pending for admin",
        )

        ModerationRequest.objects.create(
            submitted_by=self.admin,
            channel_identifier="@approved_for_admin",
            channel_by=approved_channel,
            category="Технологии",
            country="Россия",
            language="Русский",
            status="approved",
        )
        ModerationRequest.objects.create(
            submitted_by=self.admin,
            channel_identifier="@pending_for_admin",
            channel_by=pending_channel,
            category="Технологии",
            country="Россия",
            language="Русский",
            status="pending",
        )

        response = self.client.get(
            self.url,
            HTTP_ACCEPT="application/json",
            HTTP_X_INERTIA="true",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["component"], "AdminChannels")
        self.assertEqual(
            payload["props"]["channels"],
            [
                {
                    "channelId": 2001,
                    "username": "approved_for_admin",
                    "title": "Approved for admin",
                    "category": "Технологии",
                    "isVerified": True,
                    "subscribers": 1250,
                }
            ],
        )
        self.assertIn("Технологии", payload["props"]["categories"])
        self.assertNotIn(
            "Выберите категорию...",
            payload["props"]["categories"],
        )
        self.assertNotIn("Все категории", payload["props"]["categories"])
