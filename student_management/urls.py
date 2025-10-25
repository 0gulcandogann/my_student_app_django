from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add-user/', views.add_user_view, name='add_user'),
    path('list-users/', views.list_users_view, name='list_users'),
    path('delete-user/<uuid:user_id>/', views.delete_user_view, name='delete_user'),
    path('update-user/<uuid:user_id>/', views.update_user_view, name='update_user'),
    path('toggle-lock-user/<uuid:user_id>/', views.toggle_lock_user, name='toggle_lock_user'),
    path('add-student/', views.add_student_view, name='add_student'),
    path('list-student/', views.list_student_view, name='list_student'),
    path('delete-student/<uuid:student_id>/', views.delete_student_view, name='delete_student'),  # Changed to uuid
    path('update-student/<uuid:student_id>/', views.update_student_view, name='update_student'),  # Changed to uuid
    path('manage-learning-paths/', views.manage_learning_paths, name='manage_learning_paths'),
    path('add-learning-path/<uuid:student_id>/', views.add_learning_path, name='add_learning_path'),  # Already updated
    path('complete-learning-path/<int:path_id>/', views.complete_learning_path, name='complete_learning_path'),
    path('unauthorized/', views.unauthorized_view, name='unauthorized'),
    path('delete-learning-path/<int:path_id>/', views.delete_learning_path, name='delete_learning_path'),
    path('update-learning-path/<int:path_id>/', views.update_learning_path, name='update_learning_path'),
]