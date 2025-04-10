from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Temporarily comment out face recognition imports
# import face_recognition
import cv2
import numpy as np
from .models import Student, Attendance
from datetime import date

def home(request):
    return render(request, 'face_recognition_app/home.html')

@csrf_exempt
def mark_attendance(request):
    # Temporary placeholder response
    return JsonResponse({'status': 'info', 'message': 'System initialization in progress'})
    if request.method == 'POST':
        # Get the image from the POST request
        image = request.FILES.get('image')
        img_array = np.frombuffer(image.read(), np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        # Find faces in the image
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        
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
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
