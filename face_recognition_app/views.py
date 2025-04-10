from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import face_recognition
import cv2
import numpy as np
from .models import Student, Attendance
from datetime import date
import json
import base64
import tempfile
import os
from django.core.files import File

def home(request):
    return render(request, 'face_recognition_app/home.html')

@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            student_id = request.POST.get('student_id')
            photo_data = request.POST.get('photo')
            
            if not all([name, email, student_id, photo_data]):
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

            # Convert base64 image to numpy array
            photo_data = photo_data.split(',')[1]  # Remove data:image/jpeg;base64,
            photo_bytes = np.frombuffer(base64.b64decode(photo_data), np.uint8)
            image = cv2.imdecode(photo_bytes, cv2.IMREAD_COLOR)
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Generate face encoding
            face_encodings = face_recognition.face_encodings(rgb_image)
            
            if not face_encodings:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No face detected in the photo. Please try again.'
                })

            # Save image to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            cv2.imwrite(temp_file.name, image)
            
            # Create new student with the saved image
            with open(temp_file.name, 'rb') as f:
                student = Student.objects.create(
                    student_id=student_id,
                    name=name,
                    photo=File(f, name=f'{student_id}.jpg')
                )
                student.face_encoding = face_encodings[0].tobytes()
                student.save()

            # Clean up temporary file
            os.unlink(temp_file.name)
            
            return JsonResponse({'status': 'success'})
                
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

@csrf_exempt
def delete_student(request, student_id):
    if request.method == 'POST':
        try:
            student = Student.objects.get(id=student_id)
            student.delete()
            return JsonResponse({'status': 'success'})
        except Student.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Student not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        try:
            student.name = request.POST.get('name', student.name)
            student.student_id = request.POST.get('student_id', student.student_id)
            
            if 'photo' in request.FILES:
                photo = request.FILES['photo']
                image = face_recognition.load_image_file(photo)
                face_encodings = face_recognition.face_encodings(image)
                
                if face_encodings:
                    student.photo = photo
                    student.face_encoding = face_encodings[0].tobytes()
                    student.save()
                    return JsonResponse({'status': 'success'})
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No face detected in the photo'
                    })
            
            student.save()
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return render(request, 'face_recognition_app/edit_student.html', {'student': student})
