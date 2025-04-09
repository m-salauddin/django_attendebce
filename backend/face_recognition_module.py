import face_recognition
import numpy as np
import base64
from PIL import Image
import io
import sqlite3

def encode_face(image_data):
    # Convert base64 to image
    image = Image.open(io.BytesIO(base64.b64decode(image_data.split(',')[1])))
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    # Convert to numpy array
    image_array = np.array(image)
    # Get face encodings
    face_encodings = face_recognition.face_encodings(image_array)
    
    if len(face_encodings) == 0:
        raise ValueError("No face detected in the image")
    
    return face_encodings[0]

def register_new_face(student_id, name, face_image):
    try:
        # Get face encoding
        face_encoding = encode_face(face_image)
        
        # Store in database
        conn = sqlite3.connect("attendance.db")
        c = conn.cursor()
        c.execute("INSERT INTO students (student_id, name, face_encoding) VALUES (?, ?, ?)",
                 (student_id, name, face_encoding.tobytes()))
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error registering face: {str(e)}")
        return False

def recognize_face(face_image):
    try:
        # Get face encoding of the input image
        unknown_encoding = encode_face(face_image)
        
        # Get all stored face encodings
        conn = sqlite3.connect("attendance.db")
        c = conn.cursor()
        c.execute("SELECT student_id, face_encoding FROM students")
        stored_faces = c.fetchall()
        conn.close()
        
        # Compare with stored faces
        for student_id, stored_encoding_bytes in stored_faces:
            stored_encoding = np.frombuffer(stored_encoding_bytes, dtype=np.float64)
            match = face_recognition.compare_faces([stored_encoding], unknown_encoding, tolerance=0.6)[0]
            
            if match:
                return student_id
        
        return None
    except Exception as e:
        print(f"Error recognizing face: {str(e)}")
        return None