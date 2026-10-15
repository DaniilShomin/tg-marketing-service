from django.test import TestCase

from apps.admin.moderation.models import ModerationRequest
from apps.admin.moderation.services.admin_channels import AdminChannelsService
from apps.parser.models import TelegramChannel
from apps.users.models import User


class AdminChannelsServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="admin_channels_test",
            email="admin_channels_test@example.com",
            password="test-password",
            role="admin",
        )

        self.approved_channel = TelegramChannel.objects.create(
            channel_id=1001,
            username="approved_channel",
            title="Approved channel",
        )
        self.pending_channel = TelegramChannel.objects.create(
            channel_id=1002,
            username="pending_channel",
            title="Pending channel",
        )

        self.create_request(self.approved_channel, "approved")
        self.create_request(self.pending_channel, "pending")

    def create_request(
        self,
        channel: TelegramChannel,
        status: str,
    ) -> ModerationRequest:
        return ModerationRequest.objects.create(
            submitted_by=self.user,
            channel_identifier=f"@{channel.username}",
            channel_by=channel,
            category="Технологии",
            country="Россия",
            language="Русский",
            status=status,
        )

    def test_returns_only_approved_channels(self) -> None:
        channels = list(AdminChannelsService.get_channels())

        self.assertEqual(channels, [self.approved_channel])

    def test_does_not_duplicate_channel_with_multiple_approved_requests(
        self,
    ) -> None:
        self.create_request(self.approved_channel, "approved")

        channels = list(AdminChannelsService.get_channels())

        self.assertEqual(channels.count(self.approved_channel), 1)