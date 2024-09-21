from flask import request, render_template, redirect, url_for
from firebase_admin import db
from services.firebase_service import FirebaseService
from flask import session
class StudentController:
    @staticmethod
    def getStudent(id):
        studentInfo = db.reference(f"Students/{id}").get()
        return studentInfo
    
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
                student_info = FirebaseService.getStudent(id)
                if student_info is not None:
                    if student_info.get("password") == password and student_info.get("email") == email:
                        session['student_id']=id
                        print(session['student_id'])
                        return redirect(url_for("student", data=id, title=hash_secret_key))
                    else:
                        return render_template("student/student_login.html", data=" ❌ Email/Password Incorrect")
                else:
                    return render_template("student/student_login.html", data=" ❌ The id is not registered")
            else:
                return render_template("student/student_login.html")
        else:
            return render_template("student/student_login.html")
        
    @staticmethod
    def student(data, title):
        studentInfo, imgStudent, secondElapsed = FirebaseService.dataset(data)
        hoursElapsed = round((secondElapsed / 3600), 2)

        info = {
            "studentInfo": studentInfo,
            "lastlogin": hoursElapsed,
            "image": imgStudent,
        }
        return render_template("student/student.html", data=info)
    
    @staticmethod
    def student_attendance_list(marked_student_dict_json):
        student_info = []
        
        # if isinstance(marked_student_dict_json, dict):
        #     for teacher_id, student_ids in marked_student_dict_json.items():
        #         for student_id in list(set(student_ids)):
        #             student_info.append(FirebaseService.getStudent(student_id))
        # elif isinstance(marked_student_dict_json, list):
        #     for item in marked_student_dict_json:
        #         if isinstance(item, dict):
        #             for teacher_id, student_ids in item.items():
        #                 for student_id in list(set(student_ids)):
        #                     student_info.append(FirebaseService.getStudent(student_id))
        #         else:
        #             print("Invalid input format 111")
        #             print("Invalid item:", item)
        # else:
        #     print("Invalid input format 222")
        #     print("Input data:", marked_student_dict_json)
        
        for student_id in list(set(marked_student_dict_json)):
            student_info.append(FirebaseService.getStudent(student_id))

        return render_template("student_attendance_list.html", data=student_info)




