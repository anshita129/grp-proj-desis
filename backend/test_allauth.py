import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from allauth.socialaccount.models import SocialLogin, SocialAccount
from allauth.socialaccount.adapter import get_adapter
from django.contrib.auth import get_user_model
from django.test import RequestFactory
import traceback

User = get_user_model()
req = RequestFactory().get('/')
req.session = {}

sl = SocialLogin()
sl.user = User(email='test.auto.signup@gmail.com')
sl.account = SocialAccount(provider='google', uid='123456789')

try:
    get_adapter().save_user(req, sl, form=None)
    print("User saved successfully!")
    print(sl.user.username)
except Exception as e:
    print("FAILED TO SAVE USER:")
    traceback.print_exc()

