# student_management/views.py

import logging
import os
import re
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .forms import LearningPathForm, StudentForm
from .models import User, Student, LearningPath
from .utils import hash_password, verify_password

# Set up logging
logger = logging.getLogger(__name__)

# Utility Functions
def validate_password(password):
    """Validate a password against security requirements."""
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(char.islower() for char in password):
        errors.append("Password must contain at least one lowercase letter.")
    if not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character (e.g., !@#$%^&*).")
    if ' ' in password:
        errors.append("Password cannot contain spaces.")
    return errors

def save_student_photo(student_id, photo):
    """Save a student's photo and return the relative path."""
    filename = f"{student_id}_{photo.name}"
    photo_path = os.path.join('student_photos', filename)
    full_path = os.path.join(settings.MEDIA_ROOT, photo_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'wb+') as destination:
        for chunk in photo.chunks():
            destination.write(chunk)
    return photo_path

# User Authentication Views
def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return render(request, 'login.html')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')

        if not user.is_admin and user.is_locked:
            messages.error(request, 'Your account is locked. Please contact an admin.')
            return render(request, 'login.html')

        if verify_password(password, user.password):
            user.failed_login_attempts = 0
            user.last_login = timezone.now()
            user.save()
            request.session['user_id'] = str(user.id)  # Store as string for session
            request.session['user_email'] = user.email
            logger.info(f"User {email} logged in successfully.")
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            if not user.is_admin:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.is_locked = True
                    user.save()
                    logger.warning(f"Account {email} locked due to too many failed login attempts.")
                    messages.error(request, 'Your account has been locked due to too many failed login attempts. Please contact an admin.')
                else:
                    user.save()
                    messages.error(request, f'Invalid email or password. Attempt {user.failed_login_attempts}/5.')
            else:
                messages.error(request, 'Invalid email or password.')
    return render(request, 'login.html')

def register_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return render(request, 'register.html')

        if len(email) > 255:
            messages.error(request, 'Email address is too long (max 255 characters).')
            return render(request, 'register.html')

        if len(password) > 128:
            messages.error(request, 'Password is too long (max 128 characters).')
            return render(request, 'register.html')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'register.html')

        password_errors = validate_password(password)
        if password_errors:
            for error in password_errors:
                messages.error(request, error)
            return render(request, 'register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')
            return render(request, 'register.html')

        try:
            hashed_password = hash_password(password)
            user = User(
                email=email,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_admin=False
            )
            user.save()
            logger.info(f"New user registered: {email}")
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
        except ValueError as e:
            logger.error(f"Error saving user {email}: {str(e)}")
            messages.error(request, 'An error occurred while registering. Please try again.')
    return render(request, 'register.html')

def logout_view(request):
    """Handle user logout."""
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = User.objects.get(id=UUID(user_id))
            user.last_logout = timezone.now()
            user.save()
            logger.info(f"User {user.email} logged out.")
        except (User.DoesNotExist, ValueError):
            logger.warning(f"User ID {user_id} not found during logout.")
    request.session.flush()
    messages.success(request, 'Logout successful!')
    return redirect('login')

# Dashboard View
def dashboard_view(request):
    """Display the user dashboard."""
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Please log in to access the dashboard.')
        return redirect('login')

    try:
        user = User.objects.get(id=UUID(user_id))
    except (User.DoesNotExist, ValueError):
        logger.warning(f"Invalid user_id in session: {user_id}")
        messages.error(request, 'User not found. Please log in again.')
        request.session.flush()
        return redirect('login')

    context = {
        'user': user,
        'show_user_info': True
    }

    if user.is_admin:
        cozmaz_students = Student.objects.filter(level='çözmez')
        kidemli_students = Student.objects.filter(level='kıdemli')
        context['cozmaz_students'] = cozmaz_students
        context['kidemli_students'] = kidemli_students

    return render(request, 'dashboard.html', context)

# User Management Views
@admin_required
def add_user_view(request):
    """Add a new user (admin only)."""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_admin = request.POST.get('is_admin') == 'on'

        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return render(request, 'add_user.html')

        if len(email) > 255:
            messages.error(request, 'Email address is too long (max 255 characters).')
            return render(request, 'add_user.html')

        if len(password) > 128:
            messages.error(request, 'Password is too long (max 128 characters).')
            return render(request, 'add_user.html')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'add_user.html')

        password_errors = validate_password(password)
        if password_errors:
            for error in password_errors:
                messages.error(request, error)
            return render(request, 'add_user.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')
            return render(request, 'add_user.html')

        try:
            hashed_password = hash_password(password)
            user = User(
                email=email,
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_admin=is_admin
            )
            user.save()
            logger.info(f"Admin added new user: {email}")
            messages.success(request, 'User added successfully!')
            return redirect('list_users')
        except ValueError as e:
            logger.error(f"Error adding user {email}: {str(e)}")
            messages.error(request, 'An error occurred while adding the user. Please try again.')
    return render(request, 'add_user.html', {'user': request.user})

@admin_required
def list_users_view(request):
    """List all users (admin only)."""
    users = User.objects.all()
    return render(request, 'list_users.html', {'users': users})

@admin_required
def delete_user_view(request, user_id):
    """Delete a user (admin only)."""
    user = get_object_or_404(User, id=user_id)
    if user.is_admin:
        messages.error(request, 'Admin users cannot be deleted.')
        return redirect('list_users')

    if request.method == 'POST':
        user.delete()
        logger.info(f"User deleted: {user.email}")
        messages.success(request, 'User deleted successfully!')
        return redirect('list_users')

    messages.warning(request, 'Invalid request method for deleting a user.')
    return redirect('list_users')

@admin_required
def update_user_view(request, user_id):
    """Update a user's details (admin only)."""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        new_password = request.POST.get('new_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        is_admin = request.POST.get('is_admin') == 'on'

        if not email:
            messages.error(request, 'Please provide an email address.')
            return render(request, 'update_user.html', {'user': user})

        if len(email) > 255:
            messages.error(request, 'Email address is too long (max 255 characters).')
            return render(request, 'update_user.html', {'user': user})

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'update_user.html', {'user': user})

        if User.objects.filter(email=email).exclude(id=user_id).exists():
            messages.error(request, 'This email is already registered.')
            return render(request, 'update_user.html', {'user': user})

        if new_password:
            if not password:
                messages.error(request, 'Please provide the current password to change the password.')
                return render(request, 'update_user.html', {'user': user})

            if not verify_password(password, user.password):
                messages.error(request, 'Current password is incorrect.')
                return render(request, 'update_user.html', {'user': user})

            if len(new_password) > 128:
                messages.error(request, 'New password is too long (max 128 characters).')
                return render(request, 'update_user.html', {'user': user})

            password_errors = validate_password(new_password)
            if password_errors:
                for error in password_errors:
                    messages.error(request, error)
                return render(request, 'update_user.html', {'user': user})

        try:
            user.email = email
            if new_password:
                user.password = hash_password(new_password)
            user.first_name = first_name
            user.last_name = last_name
            user.is_admin = is_admin
            user.save()
            logger.info(f"User updated: {user.email}")
            messages.success(request, 'User updated successfully!')
            return redirect('list_users')
        except ValueError as e:
            logger.error(f"Error updating user {user.email}: {str(e)}")
            messages.error(request, 'An error occurred while updating the user. Please try again.')
            return render(request, 'update_user.html', {'user': user})

    return render(request, 'update_user.html', {'user': user})

@admin_required
def toggle_lock_user(request, user_id):
    """Toggle a user's lock status (admin only)."""
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        is_locked = request.POST.get('is_locked') == 'on'
        user.is_locked = is_locked
        user.failed_login_attempts = 0
        user.save()
        status = "locked" if is_locked else "unlocked"
        logger.info(f"User {user.email} {status} by admin.")
        messages.success(request, f"User {user.email} has been {status}.")
        return redirect('list_users')

    messages.warning(request, 'Invalid request method for toggling user lock status.')
    return redirect('list_users')

# Student Management Views
@admin_required
def add_student_view(request):
    """Add a new student (admin only)."""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student_id = form.cleaned_data['student_id']
            if Student.objects.filter(student_id=student_id).exists():
                messages.error(request, 'Student ID already exists.')
                return render(request, 'add_student.html', {'form': form})

            try:
                student = form.save(commit=False)
                if form.cleaned_data['photo']:
                    student.photo = save_student_photo(student_id, form.cleaned_data['photo'])
                student.save()
                logger.info(f"Student added: {student_id}")
                messages.success(request, 'Student added successfully!')
                return redirect('list_student')
            except (ValueError, OSError) as e:
                logger.error(f"Error adding student {student_id}: {str(e)}")
                messages.error(request, 'An error occurred while adding the student. Please try again.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = StudentForm()
    return render(request, 'add_student.html', {'form': form})

@admin_required
def list_student_view(request):
    """List all students (admin only)."""
    students = Student.objects.all()
    return render(request, 'list_student.html', {'students': students})

@admin_required
def delete_student_view(request, student_id):
    """Delete a student (admin only)."""
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        student.delete()
        logger.info(f"Student deleted: {student.student_id}")
        messages.success(request, 'Student deleted successfully!')
        return redirect('list_student')

    messages.warning(request, 'Invalid request method for deleting a student.')
    return redirect('list_student')

@admin_required
def update_student_view(request, student_id):
    """Update a student's details (admin only)."""
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student_id_new = form.cleaned_data['student_id']
            if Student.objects.filter(student_id=student_id_new).exclude(id=student.id).exists():
                messages.error(request, 'Student ID already exists.')
                return render(request, 'update_student.html', {'student': student, 'form': form})

            try:
                if form.cleaned_data['photo']:
                    if student.photo:
                        old_photo_path = os.path.join(settings.MEDIA_ROOT, student.photo)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    student.photo = save_student_photo(student_id_new, form.cleaned_data['photo'])
                form.save()
                logger.info(f"Student updated: {student_id_new}")
                messages.success(request, 'Student updated successfully!')
                return redirect('list_student')
            except (ValueError, OSError) as e:
                logger.error(f"Error updating student {student_id_new}: {str(e)}")
                messages.error(request, 'An error occurred while updating the student. Please try again.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = StudentForm(instance=student)
    return render(request, 'update_student.html', {'student': student, 'form': form})

# Learning Path Management Views
@admin_required
def manage_learning_paths(request):
    """Manage learning paths for students (admin only)."""
    cozmaz_students = Student.objects.filter(level='çözmez')
    kidemli_students = Student.objects.filter(level='kıdemli')
    return render(request, 'manage_learning_paths.html', {
        'cozmaz_students': cozmaz_students,
        'kidemli_students': kidemli_students,
    })

@admin_required
def add_learning_path(request, student_id):
    """Add a learning path for a student (admin only)."""
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        form = LearningPathForm(request.POST)
        if form.is_valid():
            existing_paths = LearningPath.objects.filter(student=student)
            max_order = existing_paths.aggregate(Max('order'))['order__max'] or 0
            new_order = max_order + 1

            learning_path = form.save(commit=False)
            learning_path.student = student
            learning_path.order = new_order
            learning_path.save()
            logger.info(f"Learning path added for student {student.student_id}: {learning_path.task_name}")
            messages.success(request, f"New learning path stage added to {student.first_name} {student.last_name}!")
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = LearningPathForm()
    return render(request, 'add_learning_path.html', {'form': form, 'student': student})

@admin_required
def complete_learning_path(request, path_id):
    """Mark a learning path as completed (admin only)."""
    if request.method == 'POST':
        path = get_object_or_404(LearningPath, id=path_id)
        path.is_completed = True
        path.save()
        logger.info(f"Learning path completed: {path.id}")
        messages.success(request, "Learning path marked as completed!")
        return redirect('dashboard')

    messages.warning(request, 'Invalid request method for completing a learning path.')
    return redirect('dashboard')

@require_POST
def delete_learning_path(request, path_id):
    """Delete a learning path (admin only)."""
    try:
        path = get_object_or_404(LearningPath, id=path_id)
        path.delete()
        logger.info(f"Learning path deleted: {path_id}")
        messages.success(request, "Learning path stage deleted successfully.")
        return JsonResponse({'status': 'success'})
    except (LearningPath.DoesNotExist, ValueError) as e:
        logger.error(f"Error deleting learning path {path_id}: {str(e)}")
        messages.error(request, f"Error deleting learning path stage: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@admin_required
def update_learning_path(request, path_id):
    """Update a learning path (admin only)."""
    path = get_object_or_404(LearningPath, id=path_id)
    if request.method == 'POST':
        form = LearningPathForm(request.POST, instance=path)
        if form.is_valid():
            form.save()
            logger.info(f"Learning path updated: {path_id}")
            messages.success(request, "Learning path stage updated successfully.")
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': form.errors.as_json()}, status=400)
    else:
        form = LearningPathForm(instance=path)
        return render(request, 'update_learning_path.html', {'form': form, 'path_id': path_id})

# Miscellaneous Views
def unauthorized_view(request):
    """Display unauthorized access page."""
    return render(request, 'unauthorized.html')