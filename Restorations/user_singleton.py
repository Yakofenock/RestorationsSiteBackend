from django.contrib.auth.models import User


# Only for tests:
class UserSingleton:
    _instance = None
    _username = 'SingeltonUser'

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            user, created = User.objects.get_or_create(username=cls._username)
            cls._instance = user

        return cls._instance