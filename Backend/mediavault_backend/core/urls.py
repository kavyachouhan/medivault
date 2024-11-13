from django.urls import path
from .views import SignupView, RegisterUserView, VerifyEmailView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('api/register/', RegisterUserView.as_view(), name='api-register'),
    path('api/verify-email/', VerifyEmailView.as_view(), name='api-verify-email'),
]