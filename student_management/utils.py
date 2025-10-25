# student_management/utils.py

from django.contrib.auth.hashers import make_password, check_password

def hash_password(password):
    return make_password(password, hasher='pbkdf2_sha256')

def verify_password(password, hashed_password):
    return check_password(password, hashed_password)