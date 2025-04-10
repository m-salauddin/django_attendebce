from django.db import models

class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='student_photos/')
    face_encoding = models.BinaryField(null=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'date']

    def __str__(self):
        return f"{self.student.name} - {self.date}"
