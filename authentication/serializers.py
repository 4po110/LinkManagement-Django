from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)

        # Add extra responses here
        data['user_id'] = self.user.id
        data['username'] = self.user.username

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        return data