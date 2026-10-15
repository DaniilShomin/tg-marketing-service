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

    def test_update_category_saves_valid_category(self) -> None:
        self.client.force_login(self.admin)
        channel = TelegramChannel.objects.create(
            channel_id=2003,
            username="category_update_test",
            title="Category update test",
            category="Новости и СМИ",
        )
        ModerationRequest.objects.create(
            submitted_by=self.admin,
            channel_identifier="@category_update_test",
            channel_by=channel,
            category="Новости и СМИ",
            country="Россия",
            language="Русский",
            status="approved",
        )

        response = self.client.post(
            reverse("admin_moderation:channel_category"),
            {
                "channel_id": channel.channel_id,
                "category": "Технологии",
            },
        )

        self.assertEqual(response.status_code, 302)
        channel.refresh_from_db()
        self.assertEqual(channel.category, "Технологии")

    def test_update_category_rejects_invalid_category(self) -> None:
        self.client.force_login(self.admin)
        channel = TelegramChannel.objects.create(
            channel_id=2004,
            username="invalid_category_test",
            title="Invalid category test",
            category="Новости и СМИ",
        )

        response = self.client.post(
            reverse("admin_moderation:channel_category"),
            {
                "channel_id": channel.channel_id,
                "category": "Несуществующая категория",
            },
        )

        self.assertEqual(response.status_code, 400)
        channel.refresh_from_db()
        self.assertEqual(channel.category, "Новости и СМИ")

    def test_update_category_requires_admin(self) -> None:
        channel = TelegramChannel.objects.create(
            channel_id=2005,
            username="category_rbac_test",
            title="Category RBAC test",
        )
        response = self.client.post(
            reverse("admin_moderation:channel_category"),
            {
                "channel_id": channel.channel_id,
                "category": "Технологии",
            },
        )

        self.assertEqual(response.status_code, 403)
        channel.refresh_from_db()
        self.assertIsNone(channel.category)
