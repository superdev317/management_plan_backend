from .models import User

from rest_framework import serializers


class UserCheckEmailPhoneApiMixin:
    """
    Mixin class that check if email and phone are unique
    """
    def validate_email(self, value):
        if value:
            try:
                User.objects.get(email=value.lower())
                raise serializers.ValidationError(
                    'This email has already been registered.'
                )
            except User.DoesNotExist:
                pass
        return value

    def validate_phone(self, value):
        if value:
            try:
                User.objects.get(
                    userprofile__phone_number=value, is_active=True
                )
                raise serializers.ValidationError(
                    'This phone has already been registered.'
                )
            except User.DoesNotExist:
                pass
        return value

    def validate_user_name(self, value):
        if value:
            try:
                User.objects.get(user_name=value)
                raise serializers.ValidationError(
                    'This username has already been registered.'
                )
            except User.DoesNotExist:
                pass
        return value

    def validate(self, attrs):
        if not attrs.get('email') and not attrs.get('phone') and not attrs.get('user_name'):
            raise serializers.ValidationError('Please set email or phone or username')
        return attrs

class UserCheckIdproofApiMixin:
    """
    Mixin class that check if Id proof are unique and should not be blank.
    """
    def validate_passport_photo(self, value):
        if value:
            try:
                User.objects.get(
                    userprofile__passport_photo=value, is_active=True
                )
                raise serializers.ValidationError(
                    'This passport photo has already been registered.'
                )
            except User.DoesNotExist:
                pass
        return value

    def validate_driver_license_photo(self, value):
        if value:
            try:
                User.objects.get(
                    userprofile__driver_license_photo=value, is_active=True
                )
                raise serializers.ValidationError(
                    'This passport photo has already been registered.'
                )
            except User.DoesNotExist:
                pass
        return value

    def validate(self, attrs):
        if not attrs.get('driver_license_photo') and not attrs.get('passport_photo'):
            raise serializers.ValidationError('Please upload passport or driver license')
        return attrs

class UserCheckProviderSocialMediaApiMixin:

    """
    Mixin class that check if provider and social media id should not be blank.
    """

    def validate_provider(self, attrs):
        if not attrs.get('provider'):
            raise serializers.ValidationError('Please set provider ')
        return attrs

    def validate_social(self, attrs):
        if not attrs.get('social_id'):
            raise serializers.ValidationError('Please set social id')
        return attrs

    def validate(self, attrs):
        if not attrs.get('email') and not attrs.get('phone'):
            raise serializers.ValidationError('Please set email or phone')
        return attrs