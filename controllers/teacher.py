from flask import request, render_template, redirect, url_for
from .Image_processing import ImageProcessing
from services.firebase_service import FirebaseService
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from flask import session
class TeacherController:
    
    @staticmethod
    def login():
        if request.method == "POST":
            form = request.form
            id = form.get("id_number", False)
            email = form.get("email", False)
            password = form.get("password", False)

            if id:
                secret_key = f"{id}{email}{password}"
                hash_secret_key = str(hash(secret_key))
                teacher_info = FirebaseService.getTeacher(id)
                if teacher_info is not None:
                    if teacher_info.get("password") == password and teacher_info.get("email") == email:
                        session['teacher_id'] = id
                        print(session['teacher_id'])
                        return redirect(url_for("teacher_attendance_list", data=id, title=hash_secret_key))
                    else:
                        return render_template("teacher/teacher_login.html", data=" ❌ Email/Password Incorrect")
                else:
                    return render_template("teacher/teacher_login.html", data=" ❌ The id is not registered")
            else:
                return render_template("teacher/teacher_login.html")
        else:
            return render_template("teacher/teacher_login.html")
    
    
    @staticmethod
    def teacher_attendance_list(already_marked_id_teacher):
        if request.method == "POST":
            if request.form.get("btn_teacher") == "KEY_2": # Xóa hết danh sách học sinh điểm danh ở trang admin
                already_marked_id_teacher.clear()  # Bạn cần định nghĩa already_marked_id_teacher
                return redirect(url_for('teacher_attendance_list'))
        else:
            student_info = []
            for i in list(set(already_marked_id_teacher)):
                student_info.append(FirebaseService.getStudent(i))
            return render_template("teacher/teacher_attendance_list.html", data=student_info)
    
    @staticmethod
    def teacher():
        return render_template("teacher/teacher.html")
    
    