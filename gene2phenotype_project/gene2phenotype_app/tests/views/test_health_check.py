from unittest.mock import MagicMock, patch

from django.db import DatabaseError, InterfaceError
from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    def test_health_check_returns_healthy_status(self):
        response = self.client.get(reverse("health_check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_health_check_only_allows_safe_methods(self):
        response = self.client.post(reverse("health_check"))

        self.assertEqual(response.status_code, 405)


class ReadinessCheckTests(TestCase):
    def test_readiness_check_returns_ready_when_database_is_available(self):
        cursor = MagicMock()
        cursor_context = MagicMock()
        cursor_context.__enter__.return_value = cursor

        with patch(
            "gene2phenotype_app.views.health_check.connection.cursor",
            return_value=cursor_context,
        ):
            response = self.client.get(reverse("readiness_check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ready", "database": "connected"},
        )
        cursor.execute.assert_called_once_with("SELECT 1")

    def test_readiness_check_returns_503_for_database_error(self):
        with patch(
            "gene2phenotype_app.views.health_check.connection.cursor",
            side_effect=DatabaseError,
        ):
            response = self.client.get(reverse("readiness_check"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "database": "unavailable"},
        )

    def test_readiness_check_returns_503_for_interface_error(self):
        with patch(
            "gene2phenotype_app.views.health_check.connection.cursor",
            side_effect=InterfaceError,
        ):
            response = self.client.get(reverse("readiness_check"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "not_ready", "database": "unavailable"},
        )

    def test_readiness_check_only_allows_safe_methods(self):
        response = self.client.post(reverse("readiness_check"))

        self.assertEqual(response.status_code, 405)
