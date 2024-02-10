from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.http import JsonResponse


def check_cred(request: Request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not all([username, password]):
        raise ValidationError({'detail': 'username or password not specified'})

    return username, password


@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({})


@method_decorator(csrf_protect, name='dispatch')
class SignupView(APIView):
    def post(self, request: Request):
        '''
        Method used to sugnup.
        requires JSON body {
	        "username": value,
	        "password": value
        }
        '''

        username, password = check_cred(request)

        if User.objects.filter(username=username).exists():
            raise ValidationError({'detail': 'username is already taken'})

        user = User.objects.create_user(username=username, password=password)
        user = User.objects.get(id=user.id)
        login(request, user)
        return Response({'user_id': user.id, "is_staff": user.is_staff})


@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    def post(self, request: Request):
        '''
        Method used to login.
        requires JSON body {
            "username": value,
            "password": value
        }
        '''

        username, password = check_cred(request)
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response({'user_id': user.id, "is_staff": user.is_staff})  # User id isn't really used

        raise AuthenticationFailed({'detail': 'authentication failed'})


@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request):
        '''
        Method used to logout.
        doesnt need body
        '''
        logout(request)
        return Response({})

