from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

User = get_user_model()

class UsersAuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.email = 'testpilot@tabflow.dev'
        self.password = 'StrongP@ssw0rd!'
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password
        )
        self.token = Token.objects.create(user=self.user)

    def test_user_creation_auto_generates_api_key_and_username(self):
        self.assertTrue(bool(self.user.api_key))
        self.assertEqual(len(self.user.api_key), 48)  # secrets.token_hex(24) -> 48 chars
        self.assertEqual(self.user.username, 'testpilot')

    def test_register_view_success(self):
        register_data = {
            'email': 'newuser@tabflow.dev',
            'password': 'NewUserSecret123!'
        }
        response = self.client.post('/api/auth/register/', register_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@tabflow.dev')
        self.assertTrue(User.objects.filter(email='newuser@tabflow.dev').exists())

    def test_register_view_duplicate_email_fails(self):
        duplicate_data = {
            'email': self.email,
            'password': 'AnotherPassword123!'
        }
        response = self.client.post('/api/auth/register/', duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_view_success_and_failure(self):
        # Successful login
        login_resp = self.client.post('/api/auth/login/', {
            'email': self.email,
            'password': self.password
        }, format='json')
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(login_resp.data['token'], self.token.key)

        # Invalid password
        fail_resp = self.client.post('/api/auth/login/', {
            'email': self.email,
            'password': 'WrongPassword!'
        }, format='json')
        self.assertEqual(fail_resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_view_requires_authentication(self):
        # Without credentials -> 401
        unauth_resp = self.client.get('/api/auth/me/')
        self.assertEqual(unauth_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # With credentials -> 200
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        auth_resp = self.client.get('/api/auth/me/')
        self.assertEqual(auth_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_resp.data['email'], self.email)

    def test_verify_password_produces_valid_vault_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Correct password
        correct_resp = self.client.post('/api/auth/verify-password/', {
            'password': self.password
        }, format='json')
        self.assertEqual(correct_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(correct_resp.data.get('valid'))
        self.assertTrue(bool(correct_resp.data.get('vault_token')))

        # Wrong password
        wrong_resp = self.client.post('/api/auth/verify-password/', {
            'password': 'TotallyWrongPassword'
        }, format='json')
        self.assertEqual(wrong_resp.status_code, status.HTTP_200_OK)
        self.assertFalse(wrong_resp.data.get('valid'))
        self.assertIsNone(wrong_resp.data.get('vault_token'))
