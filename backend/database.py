import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.db_file = "attendance.db"
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # Create students table
        c.execute('''CREATE TABLE IF NOT EXISTS students
                    (student_id TEXT PRIMARY KEY,
                     name TEXT NOT NULL,
                     face_encoding BLOB)''')
        
        # Create attendance table
        c.execute('''CREATE TABLE IF NOT EXISTS attendance
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     student_id TEXT,
                     timestamp DATETIME,
                     FOREIGN KEY (student_id) REFERENCES students(student_id))''')
        
        conn.commit()
        conn.close()

    def mark_attendance(self, student_id, timestamp):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("INSERT INTO attendance (student_id, timestamp) VALUES (?, ?)",
                 (student_id, timestamp))
        conn.commit()
        conn.close()

    def get_attendance_log(self, date):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("""
            SELECT s.student_id, s.name, a.timestamp 
            FROM attendance a 
            JOIN students s ON a.student_id = s.student_id 
            WHERE date(a.timestamp) = date(?)
        """, (date,))
        logs = [{"student_id": row[0], "name": row[1], "timestamp": row[2]} 
                for row in c.fetchall()]
        conn.close()
        return logs

    def get_all_students(self):
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT student_id, name FROM students")
        students = [{"student_id": row[0], "name": row[1]} for row in c.fetchall()]
        conn.close()
        return students