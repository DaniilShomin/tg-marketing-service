from apps.admin.moderation.dto.admin_channels_dto import (
    AdminChannelData,
    AdminChannelsDTO,
)
from apps.parser.forms import ChannelParseForm
from apps.parser.models import TelegramChannel


class AdminChannelsService:
    """Подготавливает список одобренных каналов для админки."""

    @staticmethod
    def get_channels() -> list[TelegramChannel]:
        return list(
            TelegramChannel.objects.filter(
                moderation_requests__status="approved"
            )
            .distinct()
            .order_by("title", "channel_id")
        )

    @staticmethod
    def get_categories() -> list[str]:
        return [
            value
            for value, _label in (
                ChannelParseForm.base_fields["category"].choices
            )
            if value not in ("Выберите категорию...", "Все категории")
        ]

    @classmethod
    def build_dto(cls) -> AdminChannelsDTO:
        channels = [
            AdminChannelData(
                channelId=channel.channel_id,
                username=channel.username or "",
                title=channel.title,
                category=channel.category or "",
                isVerified=channel.is_verified,
                subscribers=channel.participants_count,
            )
            for channel in cls.get_channels()
        ]

        return AdminChannelsDTO(
            channels=channels,
            categories=cls.get_categories(),
        )