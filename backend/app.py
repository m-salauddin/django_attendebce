from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import face_recognition_module as frm
from database import Database

app = Flask(__name__)
CORS(app)
db = Database()

@app.route('/api/register', methods=['POST'])
def register_face():
    try:
        data = request.json
        student_id = data.get('student_id')
        name = data.get('name')
        face_image = data.get('face_image')  # Base64 encoded image
        
        # Process and store face encoding
        success = frm.register_new_face(student_id, name, face_image)
        
        if success:
            return jsonify({"message": "Face registered successfully"}), 200
        return jsonify({"error": "Failed to register face"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mark-attendance', methods=['POST'])
def mark_attendance():
    try:
        face_image = request.json.get('face_image')  # Base64 encoded image
        
        # Recognize face and get student ID
        student_id = frm.recognize_face(face_image)
        
        if student_id:
            # Mark attendance in database
            timestamp = datetime.now()
            db.mark_attendance(student_id, timestamp)
            return jsonify({"message": "Attendance marked successfully"}), 200
        
        return jsonify({"error": "Face not recognized"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/attendance-log', methods=['GET'])
def get_attendance_log():
    try:
        date = request.args.get('date')
        logs = db.get_attendance_log(date)
        return jsonify(logs), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students', methods=['GET'])
def get_students():
    try:
        students = db.get_all_students()
        return jsonify(students), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)