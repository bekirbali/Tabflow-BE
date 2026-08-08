from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LinkViewSet, AddLinkByKeyView

router = DefaultRouter()
router.register(r'', LinkViewSet, basename='link')

urlpatterns = [
    path('add-by-key/', AddLinkByKeyView.as_view(), name='add_by_key'),
    path('', include(router.urls)),
]
