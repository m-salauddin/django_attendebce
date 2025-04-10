from django.contrib import admin
from django.urls import path
from face_recognition_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('students/', views.students, name='students'),
    path('attendance/', views.attendance, name='attendance'),
    path('details/', views.attendance_details, name='details'),
    path('camera/', views.camera_config, name='camera'),
    path('mark_attendance/', views.mark_attendance, name='mark_attendance'),
]
