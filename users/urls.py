from django.urls import path
from .views import RegisterView, LoginView, MeView, VerifyPasswordView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', MeView.as_view(), name='me'),
    path('verify-password/', VerifyPasswordView.as_view(), name='verify-password'),
]
