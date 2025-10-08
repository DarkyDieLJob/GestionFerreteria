"""Tests for core_auth serializers."""
from django.test import TestCase
from core_auth.adapters.serializers import Core_authSerializer
from core_auth.adapters.models import Core_auth


class TestCoreAuthSerializer(TestCase):
    """Test cases for Core_authSerializer."""

    def test_serializer_contains_expected_fields(self):
        """Test that the serializer contains the expected fields."""
        # Create a test instance
        core_auth = Core_auth.objects.create(name="Test Core Auth")
        
        # Create serializer instance
        serializer = Core_authSerializer(instance=core_auth)
        
        # Check that the serializer data matches the expected fields
        expected_fields = {'id', 'name', 'created_at'}
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_serializer_valid_data(self):
        """Test that the serializer validates correct data."""
        data = {
            'name': 'Test Core Auth'
        }
        serializer = Core_authSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Check that the data is correctly serialized
        self.assertEqual(serializer.validated_data['name'], 'Test Core Auth')

    def test_serializer_missing_required_field(self):
        """Test that the serializer handles missing required fields."""
        data = {}
        serializer = Core_authSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_serializer_update(self):
        """Test updating an instance with the serializer."""
        # Create initial instance
        core_auth = Core_auth.objects.create(name="Initial Name")
        
        # Update data
        data = {
            'name': 'Updated Name'
        }
        
        # Update instance
        serializer = Core_authSerializer(instance=core_auth, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_core_auth = serializer.save()
        
        # Check that the instance was updated
        self.assertEqual(updated_core_auth.name, 'Updated Name')
        self.assertEqual(Core_auth.objects.count(), 1)
        self.assertEqual(Core_auth.objects.first().name, 'Updated Name')
