from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import User, EmailVerification

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email',)

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            is_active=False
        )
        return user

class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(required=False, min_length=6, max_length=6)