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
import os
from django.conf import settings
from django.core.files.base import ContentFile
import io
from django.utils import timezone

def home(request):
    return render(request, 'face_recognition_app/home.html')

@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            student_id = request.POST.get('student_id')
            photo_data = request.POST.get('photo')
            
            if not all([name, student_id, photo_data]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'All fields are required'
                })

            try:
                # Process base64 image
                if 'data:image' in photo_data:
                    photo_data = photo_data.split('base64,')[1]
                
                # Convert base64 to image
                photo_bytes = base64.b64decode(photo_data)
                nparr = np.frombuffer(photo_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if image is None:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid image format'
                    })

                # Convert BGR to RGB for face_recognition
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Detect faces with more lenient parameters
                face_locations = face_recognition.face_locations(rgb_image, model="hog", number_of_times_to_upsample=2)
                if not face_locations:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'No face detected in the photo. Please ensure good lighting and try again.'
                    })
                
                # Generate face encodings with adjusted tolerance
                face_encodings = face_recognition.face_encodings(rgb_image, face_locations, num_jitters=2)
                
                if not face_encodings:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Could not process face features. Please try again with better lighting.'
                    })

                # Save student with photo
                try:
                    student = Student.objects.create(
                        name=name,
                        student_id=student_id
                    )
                    
                    # Save photo
                    photo_name = f'{student_id}.jpg'
                    student.photo.save(photo_name, ContentFile(photo_bytes), save=True)
                    student.face_encoding = face_encodings[0].tobytes()
                    student.save()
                    
                    return JsonResponse({'status': 'success'})
                except Exception as e:
                    if student:
                        student.delete()  # Cleanup if photo save fails
                    raise e
                
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error processing image: {str(e)}'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Registration failed: {str(e)}'
            })
            
    return render(request, 'face_recognition_app/register.html')

def students(request):
    students_list = Student.objects.all()
    for student in students_list:
        if student.photo:
            # Convert photo to base64 for display
            image_data = base64.b64encode(student.photo.read()).decode('utf-8')
            student.photo_base64 = f"data:image/jpeg;base64,{image_data}"
    return render(request, 'face_recognition_app/students.html', {'students': students_list})

@csrf_exempt
def delete_student(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
        student.delete()
        return JsonResponse({'status': 'success'})
    except Student.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Student not found'})

@csrf_exempt
def edit_student(request, student_id):
    if request.method == 'POST':
        try:
            student = Student.objects.get(id=student_id)
            name = request.POST.get('name')
            new_student_id = request.POST.get('student_id')
            photo_data = request.POST.get('photo')

            if name:
                student.name = name
            if new_student_id:
                student.student_id = new_student_id
            
            if photo_data and 'data:image' in photo_data:
                photo_data = photo_data.split('base64,')[1]
                photo_bytes = base64.b64decode(photo_data)
                
                # Process new face encoding
                nparr = np.frombuffer(photo_bytes, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_image)
                face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
                
                if face_encodings:
                    student.face_encoding = face_encodings[0].tobytes()
                    photo_name = f'{student.student_id}.jpg'
                    student.photo.save(photo_name, ContentFile(photo_bytes), save=True)

            student.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def attendance(request):
    return render(request, 'face_recognition_app/attendance.html')

def attendance_details(request):
    students = Student.objects.all()
    attendance_list = Attendance.objects.all().order_by('-date', '-time')
    return render(request, 'face_recognition_app/details.html', {
        'attendance': attendance_list,
        'students': students
    })

@csrf_exempt
def filter_attendance(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    student_id = request.GET.get('student_id')
    
    queryset = Attendance.objects.all()
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    if student_id:
        queryset = queryset.filter(student_id=student_id)
        
    attendance_data = [{
        'student_name': record.student.name,
        'student_id': record.student.student_id,
        'date': record.date.strftime('%Y-%m-%d'),
        'time': record.time.strftime('%H:%M:%S')
    } for record in queryset]
    
    return JsonResponse({'attendance': attendance_data})

def export_attendance(request):
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Student ID', 'Date', 'Time', 'Status'])
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    student_id = request.GET.get('student_id')
    
    queryset = Attendance.objects.all()
    
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    if student_id:
        queryset = queryset.filter(student_id=student_id)
    
    for record in queryset:
        writer.writerow([
            record.student.name,
            record.student.student_id,
            record.date,
            record.time.strftime('%H:%M:%S'),
            'Present'
        ])
    
    return response

def camera_config(request):
    return render(request, 'face_recognition_app/camera.html')

@csrf_exempt
def mark_attendance(request):
    if request.method == 'POST':
        try:
            image = request.FILES.get('image')
            img_array = np.frombuffer(image.read(), np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Enhanced face detection parameters
            face_locations = face_recognition.face_locations(
                rgb_frame,
                model="hog",  # Use HOG model for better performance
                number_of_times_to_upsample=2  # Increase detection sensitivity
            )
            
            # Enhanced face encoding parameters
            face_encodings = face_recognition.face_encodings(
                rgb_frame,
                face_locations,
                num_jitters=2,  # Increase accuracy with more samples
                model="large"  # Use large model for better accuracy
            )
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                students = Student.objects.all()
                for student in students:
                    stored_encoding = np.frombuffer(student.face_encoding)
                    # Increased tolerance for better matching
                    matches = face_recognition.compare_faces(
                        [stored_encoding],
                        face_encoding,
                        tolerance=0.5  # Decreased tolerance for more strict matching
                    )
                    
                    if matches[0]:
                        # Add name label
                        cv2.putText(frame, student.name, (left + 6, top - 6), 
                                  cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255), 1)
                        
                        # Mark attendance
                        Attendance.objects.get_or_create(
                            student=student,
                            date=date.today()
                        )
                        
                        attendance_marked = True
                        
                        # Convert frame to base64 for response
                        _, buffer = cv2.imencode('.jpg', frame)
                        frame_b64 = base64.b64encode(buffer).decode('utf-8')
                        
                        return JsonResponse({
                            'status': 'success',
                            'student': student.name,
                            'processed_image': frame_b64
                        })
            
            # If faces detected but no match
            if face_locations:
                _, buffer = cv2.imencode('.jpg', frame)
                frame_b64 = base64.b64encode(buffer).decode('utf-8')
                return JsonResponse({
                    'status': 'error',
                    'message': 'No matching face found',
                    'processed_image': frame_b64
                })
            
            return JsonResponse({
                'status': 'error',
                'message': 'No face detected'
            })
            
        except Exception as e:
            print(f"Error processing attendance: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error processing attendance'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })