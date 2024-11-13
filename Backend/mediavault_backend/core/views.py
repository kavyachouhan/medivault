# core/views.py
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.html import strip_tags
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from .models import User, EmailVerification
from .serializers import UserRegistrationSerializer, EmailVerificationSerializer
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.views.generic import TemplateView

class SignupView(TemplateView):
    template_name = 'signup.html'

class RegisterUserView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate verification code
            verification = EmailVerification.objects.create(
                user=user,
                code=EmailVerification.generate_code(),
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
            # Prepare email content
            context = {
                'verification_code': verification.code,
            }
            html_message = render_to_string('email/verification_email.html', context)
            plain_message = strip_tags(html_message)
            
            # Send verification email
            try:
                send_mail(
                    subject='Verify Your MediaVault Account',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                return Response({
                    'message': 'Verification code sent to your email',
                    'email': user.email
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                user.delete()  # Rollback user creation if email fails
                return Response({
                    'message': 'Failed to send verification email'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            
            try:
                user = User.objects.get(email=email)
                verification = EmailVerification.objects.filter(
                    user=user,
                    code=code,
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).latest('created_at')
                
                verification.is_used = True
                verification.save()
                
                user.is_active = True
                user.save()
                
                # Send welcome email
                welcome_html = render_to_string('email/welcome_email.html', {
                    'email': user.email
                })
                welcome_text = strip_tags(welcome_html)
                
                send_mail(
                    subject='Welcome to MediaVault!',
                    message=welcome_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=welcome_html,
                    fail_silently=True,
                )
                
                return Response({
                    'message': 'Email verified successfully'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'message': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
            except EmailVerification.DoesNotExist:
                return Response({
                    'message': 'Invalid or expired verification code'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)