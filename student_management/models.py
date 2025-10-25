# student_management/models.py

from django.db import models
from django.utils import timezone
import uuid

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    last_logout = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'users'
        managed = False

class Student(models.Model):
    LEVEL_CHOICES = (
        ('çözmez', 'Çözmez'),
        ('kıdemli', 'Kıdemli'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    photo = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='çözmez')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"

    class Meta:
        db_table = 'students'
        ordering = ['-created_at']
        managed = False

class LearningPath(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='learning_paths')
    task_name = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    estimated_end_date = models.DateTimeField()
    used_leave = models.CharField(max_length=50, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    required_duration = models.CharField(max_length=50)
    is_completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.student} - {self.task_name} (Order: {self.order})"

    class Meta:
        db_table = 'student_management_learningpath'
        ordering = ['order']
        managed = False

#class Notification(models.Model):
#    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
#    message = models.TextField()
#    created_at = models.DateTimeField(default=timezone.now)
#    is_read = models.BooleanField(default=False)
#
#    def __str__(self):
#        return f"Notification for {self.user.email}: {self.message}"
#
#    class Meta:
#        db_table = 'notifications'
#        ordering = ['-created_at']
#        managed = False