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

            try:
                # Convert base64 image to numpy array
                photo_data = photo_data.split(',')[1]  # Remove data:image/jpeg;base64,
                photo_bytes = np.frombuffer(base64.b64decode(photo_data), np.uint8)
                image = cv2.imdecode(photo_bytes, cv2.IMREAD_COLOR)
                
                if image is None:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid image format'
                    })
                
                # Ensure image is in correct format
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Generate face encoding
                face_locations = face_recognition.face_locations(image)
                if not face_locations:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No face detected in the photo. Please try again.'
                    })
                
                face_encodings = face_recognition.face_encodings(image, face_locations)
                
                if not face_encodings:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Could not process face in the photo. Please try again.'
                    })

                # Convert back to BGR for saving
                save_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
                # Save image to temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                cv2.imwrite(temp_file.name, save_image)
                
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
                
            except cv2.error as e:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Error processing image. Please try a different photo.'
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
            if 'image' not in request.FILES:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No image file received'
                })

            image = request.FILES['image']
            
            # Read image file
            image_bytes = image.read()
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid image format'
                })

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces in the image
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if not face_locations:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No face detected in the image'
                })

            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Compare with known faces
                students = Student.objects.all()
                for student in students:
                    stored_encoding = np.frombuffer(student.face_encoding)
                    match = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)[0]
                    
                    if match:
                        # Mark attendance
                        attendance, created = Attendance.objects.get_or_create(
                            student=student,
                            date=date.today()
                        )
                        
                        return JsonResponse({
                            'status': 'success',
                            'student': student.name,
                            'face_location': face_location
                        })
            
            return JsonResponse({
                'status': 'error',
                'message': 'No matching student found'
            })
            
        except Exception as e:
            print(f"Error processing attendance: {str(e)}")  # For debugging
            return JsonResponse({
                'status': 'error',
                'message': 'Error processing attendance'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })
