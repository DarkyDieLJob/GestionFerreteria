import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from core_auth.models import CoreAuthProfile


@pytest.mark.django_db
def test_register_sets_dni_last4_hash(client):
    url = reverse('core_auth:register')
    data = {
        'username': 'userx',
        'email': 'userx@example.com',
        'password1': 'S3guro123!A',
        'password2': 'S3guro123!A',
        'phone_number': '12345678',
        'dni_last4': '1234',
        'terms': 'on',
    }
    resp = client.post(url, data)
    # Should redirect to login on success
    assert resp.status_code == 302
    # User created
    u = User.objects.get(username='userx')
    prof = CoreAuthProfile.objects.get(user=u)
    assert prof.dni_last4_hash
    assert prof.dni_last4_hash != '1234'
