from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from apps.group_channels.models import AutoGroupRule, Group
from apps.parser.models import TelegramChannel
from apps.users.models import User


class GroupDetailViewTest(TestCase):
    """Проверяет поведение представления детальной страницы подборки."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="test-password",
        )
        self.curator = User.objects.create_user(
            username="editor",
            email="editor@example.com",
            password="test-password",
        )

        self.group = Group.objects.create(
            name="Топ IT-каналов",
            slug="top-it",
            description="Подборка технологических каналов",
            owner=self.owner,
            curator=self.curator,
            is_editorial=True,
        )

        self.channel = TelegramChannel.objects.create(
            channel_id=100001,
            username="product_radar",
            title="Product Radar",
            participants_count=142000,
            average_views=38200,
            category="Технологии",
            country="RU",
        )

        self.group.channels.add(self.channel)

    @patch("apps.group_channels.views.inertia_render")
    def test_detail_returns_group_detail_component(
        self,
        mock_inertia_render,
    ):
        """Проверяет возврат компонента GroupDetail с данными подборки."""
        mock_inertia_render.return_value = HttpResponse("OK")

        response = self.client.get(
            reverse(
                "collection_detail",
                kwargs={"slug": self.group.slug},
            ),
        )

        self.assertEqual(response.status_code, 200)
        mock_inertia_render.assert_called_once()

        args, kwargs = mock_inertia_render.call_args

        self.assertEqual(args[1], "GroupDetail")
        self.assertEqual(
            kwargs["props"]["header"]["name"],
            self.group.name,
        )

    @patch("apps.group_channels.views.inertia_render")
    def test_header_contains_expected_fields(
        self,
        mock_inertia_render,
    ):
        """Проверяет состав и значения полей заголовка подборки."""
        mock_inertia_render.return_value = HttpResponse("OK")

        self.client.get(
            reverse(
                "collection_detail",
                kwargs={"slug": self.group.slug},
            ),
        )

        props = mock_inertia_render.call_args.kwargs["props"]
        header = props["header"]

        self.assertEqual(
            set(header),
            {
                "name",
                "description",
                "gradient_key",
                "is_editorial",
                "curator",
                "channel_count",
                "category",
            },
        )

        self.assertEqual(header["name"], "Топ IT-каналов")
        self.assertEqual(
            header["description"],
            "Подборка технологических каналов",
        )
        self.assertEqual(
            header["gradient_key"],
            f"collection-{self.group.pk}",
        )
        self.assertTrue(header["is_editorial"])
        self.assertEqual(header["curator"], "editor")
        self.assertEqual(header["channel_count"], 1)
        self.assertIsNone(header["category"])

    @patch("apps.group_channels.views.inertia_render")
    def test_channel_card_contains_expected_fields(
        self,
        mock_inertia_render,
    ):
        """Проверяет состав и значения полей карточки канала."""
        mock_inertia_render.return_value = HttpResponse("OK")

        self.client.get(
            reverse(
                "collection_detail",
                kwargs={"slug": self.group.slug},
            ),
        )

        props = mock_inertia_render.call_args.kwargs["props"]
        channels = props["channels"]

        self.assertEqual(len(channels), 1)

        self.assertEqual(
            set(channels[0]),
            {
                "title",
                "username",
                "avatar",
                "subscribers",
                "average_views",
                "category",
                "country",
            },
        )

        self.assertEqual(
            channels[0],
            {
                "title": "Product Radar",
                "username": "product_radar",
                "avatar": "",
                "subscribers": 142000,
                "average_views": 38200,
                "category": "Технологии",
                "country": "RU",
            },
        )

    @patch("apps.group_channels.views.inertia_render")
    def test_auto_collection_uses_rule_category(self, mock_inertia_render):
        """Проверяет отбор каналов автоматической подборки по категории."""
        mock_inertia_render.return_value = HttpResponse("OK")

        auto_group = Group.objects.create(
            name="Научные каналы",
            slug="science",
            owner=self.owner,
        )
        AutoGroupRule.objects.create(
            group=auto_group,
            category="Наука",
        )

        TelegramChannel.objects.create(
            channel_id=10001,
            username="science_news",
            title="Science News",
            category="Наука",
            country="RU",
        )
        other_channel = TelegramChannel.objects.create(
            channel_id=10002,
            username="travel_news",
            title="Travel News",
            category="Путешествия",
            country="RU",
        )
        auto_group.channels.add(other_channel)

        response = self.client.get(
            reverse(
                "collection_detail",
                kwargs={"slug": auto_group.slug},
            )
        )

        self.assertEqual(response.status_code, 200)

        props = mock_inertia_render.call_args.kwargs["props"]

        self.assertEqual(props["auto_category"], "Наука")
        self.assertEqual(props["header"]["category"], "Наука")
        self.assertEqual(props["header"]["channel_count"], 1)
        self.assertEqual(
            {channel["username"] for channel in props["channels"]},
            {"science_news"},
        )

    def test_unknown_slug_returns_404(self):
        """Проверяет возврат ошибки 404 для несуществующей подборки."""
        response = self.client.get(
            reverse(
                "collection_detail",
                kwargs={"slug": "does-not-exist"},
            ),
        )

        self.assertEqual(response.status_code, 404)

    @patch("apps.group_channels.views.inertia_render")
    def test_owner_of_manual_collection_gets_add_form(
        self,
        mock_inertia_render,
    ):
        """
        Проверяет доступность формы добавления каналов
        владельцу ручной подборки.
        """
        mock_inertia_render.return_value = HttpResponse("OK")
        self.client.force_login(self.owner)

        self.client.get(
            reverse(
                "collection_detail",
                kwargs={"slug": self.group.slug},
            ),
        )

        props = mock_inertia_render.call_args.kwargs["props"]

        self.assertTrue(props["is_owner"])
        self.assertIsNotNone(props["add_form"])

    @patch("apps.group_channels.views.inertia_render")
    def test_owner_of_auto_collection_has_no_add_form(
        self,
        mock_inertia_render,
    ):
        """
        Проверяет отсутствие формы добавления каналов
        у владельца автоподборки.
        """
        mock_inertia_render.return_value = HttpResponse("OK")

        auto_group = Group.objects.create(
            name="Автоподборка",
            slug="auto-collection",
            owner=self.owner,
        )

        AutoGroupRule.objects.create(
            group=auto_group,
            category="Технологии",
        )

        self.client.force_login(self.owner)

        self.client.get(
            reverse(
                "collection_detail",
                kwargs={"slug": auto_group.slug},
            ),
        )

        props = mock_inertia_render.call_args.kwargs["props"]

        self.assertTrue(props["is_owner"])
        self.assertIsNone(props["add_form"])

    @patch("apps.group_channels.views.inertia_render")
    def test_guest_is_not_owner(
        self,
        mock_inertia_render,
    ):
        """
        Проверяет отсутствие прав владельца
        у неавторизованного пользователя.
        """
        mock_inertia_render.return_value = HttpResponse("OK")

        response = self.client.get(
            reverse(
                "collection_detail",
                kwargs={"slug": self.group.slug},
            ),
        )

        self.assertEqual(response.status_code, 200)

        props = mock_inertia_render.call_args.kwargs["props"]

        self.assertFalse(props["is_owner"])

    @patch("apps.group_channels.views.inertia_render")
    def test_legacy_group_url_still_works(
        self,
        mock_inertia_render,
    ):
        """Проверяет старый URL детальной страницы."""
        mock_inertia_render.return_value = HttpResponse("OK")

        response = self.client.get(
            reverse(
                "group_channels:group_detail",
                kwargs={"slug": self.group.slug},
            ),
        )

        self.assertEqual(response.status_code, 200)

        args, _ = mock_inertia_render.call_args
        self.assertEqual(args[1], "GroupDetail")
