from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import Link

User = get_user_model()

class LinksTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='linkuser@example.com',
            password='linkpassword123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.links_url = '/api/links/'
        self.sync_url = '/api/links/sync/'
        self.key_url = '/api/links/add-by-key/'

    def test_links_crud(self):
        # 1. Create Link
        link_data = {
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'video_id': 'dQw4w9WgXcQ',
            'title': 'Never Gonna Give You Up',
            'author_name': 'Rick Astley',
            'duration': '3:32',
            'curator': '@feed_master',
            'category': 'Music'
        }
        response = self.client.post(self.links_url, link_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Never Gonna Give You Up')
        link_id = response.data['id']

        # 2. Get Links List
        get_response = self.client.get(self.links_url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_response.data), 1)

        # 3. Patch Link
        patch_response = self.client.patch(f'{self.links_url}{link_id}/', {'liked': True}, format='json')
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertTrue(patch_response.data['liked'])

        # 4. Delete Link
        delete_response = self.client.delete(f'{self.links_url}{link_id}/')
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_links_sync(self):
        # Sync a list of 2 links
        sync_data = [
            {
                'videoId': 'dQw4w9WgXcQ',
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'title': 'Never Gonna Give You Up',
                'author_name': 'Rick Astley',
                'is_watched': False,
                'liked': False,
                'bookmarked': True,
                'duration': '3:32',
                'curator': '@feed_master',
                'category': 'Music'
            },
            {
                'videoId': 'y9c_kefdQUs',
                'url': 'https://www.youtube.com/watch?v=y9c_kefdQUs',
                'title': 'Seeded Title',
                'author_name': 'Channel',
                'is_watched': True,
                'liked': True,
                'bookmarked': False,
                'duration': '5:00',
                'curator': '@feed_master',
                'category': 'Tech'
              }
        ]
        response = self.client.post(self.sync_url, sync_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Verify database has them
        self.assertEqual(Link.objects.filter(user=self.user).count(), 2)

    def test_add_by_api_key(self):
        # 1. Test using headers X-Api-Key
        self.client.credentials()  # Clear standard token auth
        add_data = {
            'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'title': 'Rick Astley via API Key',
            'author_name': 'Rick Astley'
        }
        headers = {'HTTP_X_API_KEY': self.user.api_key}
        response = self.client.post(self.key_url, add_data, format='json', **headers)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['video']['title'], 'Rick Astley via API Key')
        self.assertEqual(Link.objects.filter(user=self.user).count(), 1)
