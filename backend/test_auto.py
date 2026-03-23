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
sl.user = User(email='test.auto.signup2@gmail.com')
sl.account = SocialAccount(provider='google', uid='12345678910')
sl.email_addresses = [] # wait, the provider populates sl.email_addresses!

adapter = get_adapter()
print("is_auto_signup_allowed:", adapter.is_auto_signup_allowed(req, sl))

