from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import face_recognition
import cv2
import numpy as np
from .models import Student, Attendance
from datetime import date
import json

def home(request):
    return render(request, 'face_recognition_app/home.html')

@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            student_id = request.POST.get('student_id')
            photo = request.FILES.get('photo')
            
            if not all([name, email, student_id, photo]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'All fields are required'
                })
            
            # Check if student_id already exists
            if Student.objects.filter(student_id=student_id).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Student ID already exists'
                })
            
            # Create new student
            student = Student.objects.create(
                student_id=student_id,
                name=name,
                photo=photo
            )
            
            # Generate and save face encoding
            image = face_recognition.load_image_file(photo)
            face_encodings = face_recognition.face_encodings(image)
            
            if face_encodings:
                student.face_encoding = face_encodings[0].tobytes()
                student.save()
                return JsonResponse({'status': 'success'})
            else:
                student.delete()
                return JsonResponse({
                    'status': 'error',
                    'message': 'No face detected in the photo. Please try again.'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Registration failed: {str(e)}'
            })
            
    return render(request, 'face_recognition_app/register.html')

def students(request):
    students_list = Student.objects.all()
    return render(request, 'face_recognition_app/students.html', {'students': students_list})

def attendance(request):
    return render(request, 'face_recognition_app/attendance.html')

def attendance_details(request):
    attendance_list = Attendance.objects.all().order_by('-date', '-time')
    return render(request, 'face_recognition_app/details.html', {'attendance': attendance_list})

def camera_config(request):
    return render(request, 'face_recognition_app/camera.html')

@csrf_exempt
def mark_attendance(request):
    if request.method == 'POST':
        try:
            # Get the image from the POST request
            image = request.FILES.get('image')
            img_array = np.frombuffer(image.read(), np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces in the image
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for face_encoding in face_encodings:
                # Compare with known faces
                students = Student.objects.all()
                for student in students:
                    stored_encoding = np.frombuffer(student.face_encoding)
                    match = face_recognition.compare_faces([stored_encoding], face_encoding)[0]
                    
                    if match:
                        # Mark attendance
                        Attendance.objects.get_or_create(
                            student=student,
                            date=date.today()
                        )
                        return JsonResponse({'status': 'success', 'student': student.name})
        
            return JsonResponse({'status': 'error', 'message': 'No matching face found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
