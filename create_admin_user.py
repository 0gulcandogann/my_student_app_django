import os
import django
from django.contrib.auth.hashers import make_password

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

password = '29191156o'
hashed_password = make_password(password)
print(hashed_password)