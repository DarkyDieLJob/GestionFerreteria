"""Tests for core_auth models."""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from core_auth.adapters.models import Core_auth

User = get_user_model()


class TestUserModel(TestCase):
    """Test the user model."""

    def test_create_user(self):
        """Test creating a user with a username is successful."""
        username = "testuser"
        password = "testpass123"
        user = User.objects.create_user(username=username, password=password)

        assert user.username == username
        assert user.check_password(password)
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            "admin", "admin@example.com", "adminpass123"
        )

        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.is_active is True

    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        assert str(user) == "testuser"


class TestCoreAuthModel(TestCase):
    """Test the Core_auth model."""

    def test_create_core_auth(self):
        """Test creating a Core_auth instance is successful."""
        name = "Test Item"
        core_auth = Core_auth.objects.create(name=name)

        # Verify the instance was created with correct attributes
        assert core_auth.name == name
        assert core_auth.created_at is not None
        assert core_auth.id is not None

    def test_core_auth_str_representation(self):
        """Test Core_auth string representation."""
        name = "Test Item"
        core_auth = Core_auth.objects.create(name=name)

        assert str(core_auth) == name

    def test_created_at_auto_now_add(self):
        """Test that created_at is automatically set on creation."""
        before_creation = timezone.now()
        core_auth = Core_auth.objects.create(name="Test")
        after_creation = timezone.now()

        assert before_creation <= core_auth.created_at <= after_creation

    def test_meta_db_table(self):
        """Test the custom database table name."""
        self.assertEqual(Core_auth._meta.db_table, "core_auth_items")
