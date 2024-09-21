from flask import request, render_template, redirect, url_for, jsonify
import os
import pickle
import json
from .Image_processing import ImageProcessing
from services.firebase_service import FirebaseService
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from flask import session

class AdminController:
    
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
                admin_info = FirebaseService.getAdmin(id)
                if admin_info is not None:
                    if admin_info.get("password") == password and admin_info.get("email") == email:
                        session['admin_id'] = id
                        print(session['admin_id'])
                        return redirect(url_for("admin", data=id, title=hash_secret_key))
                    else:
                        return render_template("admin/admin_login.html", data=" ❌ Email/Password Incorrect")
                else:
                    return render_template("admin/admin_login.html", data=" ❌ The id is not registered")
            else:
                return render_template("admin/admin_login.html")
        else:
            return render_template("admin/admin_login.html")
    
    @staticmethod
    def admin():
        studentIDs, _ = ImageProcessing.findID()
        all_student_info = []
        for i in studentIDs:
            all_student_info.append(FirebaseService.getStudent(i))
        return render_template("admin/student/admin_students.html", data=all_student_info)
    
    @staticmethod
    def admin_teacher():
        teacherIDs, _ = ImageProcessing.findIDTeacher()
        all_teacher_info = []
        for i in teacherIDs:
            print(FirebaseService.getTeacher(i))
            all_teacher_info.append(FirebaseService.getTeacher(i))
        return render_template("admin/teacher/admin_teachers.html", data=all_teacher_info)
        
    @staticmethod
    def add_user():
        id = request.form.get("id", False)
        name = request.form.get("name", False)
        password = request.form.get("password", False)
        dob = request.form.get("dob", False)
        city = request.form.get("city", False)
        country = request.form.get("country", False)
        phone = request.form.get("phone", False)
        email = request.form.get("email", False)
        major = request.form.get("major", False)
        starting_year = request.form.get("starting_year", False)
        total_attendance = request.form.get("total_attendance", False)
        year = request.form.get("year", False)
        last_attendance_date = request.form.get("last_attendance_date", False)
        last_attendance_time = request.form.get("last_attendance_time", False)
        content = request.form.get("content", False)

        address = f"{city}, {country}"
        last_attendance_datetime = f"{last_attendance_date} {last_attendance_time}:00"
        year = int(year)
        total_attendance = int(total_attendance)
        starting_year = int(starting_year)

        if request.method == "POST":
            id_exist = db.reference(f"Students/{id}").get()
            if id_exist:
                return render_template("admin/student/add_student.html", message="ID already exists")
            email_exist = db.reference("Students").order_by_child("email").equal_to(email).get()
            if email_exist:
                return render_template("admin/student/add_student.html", message="Email already exists")
            image = request.files["image"]
            filename = f"{'static/Files/Images/students'}/{id}.jpg"
            image.save(os.path.join(filename))
            
        else:
            return render_template("admin/student/add_student.html")

        studentIDs, imgList = FirebaseService.add_image_database()
        encodeListKnown = ImageProcessing.findEncodings(imgList)
        encodeListKnownWithIds = [encodeListKnown, studentIDs]

        with open("EncodeFile.p", "wb") as file:
            pickle.dump(encodeListKnownWithIds, file)

        if id:
            add_student = db.reference(f"Students")
            add_student.child(id).set(
                {
                    "id": id,
                    "name": name,
                    "password": password,
                    "dob": dob,
                    "address": address,
                    "phone": phone,
                    "email": email,
                    "major": major,
                    "starting_year": starting_year,
                    "total_attendance": total_attendance,
                    "year": year,
                    "last_attendance_time": last_attendance_datetime,
                    "content": content,
                }
            )
            return render_template("admin/student/add_student.html", message = 'Added Successfully')

        return render_template("admin/student/add_student.html")
    
    @staticmethod
    def add_teacher():
        id = request.form.get("id", False)
        name = request.form.get("name", False)
        password = request.form.get("password", False)
        dob = request.form.get("dob", False)
        city = request.form.get("city", False)
        country = request.form.get("country", False)
        phone = request.form.get("phone", False)
        email = request.form.get("email", False)
        address = f"{city}, {country}"
        if request.method == "POST":
            id_exist = db.reference(f"Teachers/{id}").get()
            if id_exist:
                return render_template("admin/teacher/add_teacher.html", message="ID already exists")
            email_exist = db.reference("Teachers").order_by_child("email").equal_to(email).get()
            if email_exist:
                return render_template("admin/teacher/add_teacher.html", message="Email already exists")
            
            image = request.files["image"]
            filename = f"{'static/Files/Images/teachers'}/{id}.jpg"
            image.save(os.path.join(filename))
        else:
            return render_template("admin/teacher/add_teacher.html")

        FirebaseService.add_image_database_teacher()

        if id:
            add_teacher = db.reference(f"Teachers")
            add_teacher.child(id).set(
                {
                    "id": id,
                    "name": name,
                    "password": password,
                    "dob": dob,
                    "address": address,
                    "phone": phone,
                    "email": email,
                }
            )
            return render_template("admin/teacher/add_teacher.html", message = 'Added Successfully')

        return render_template("admin/teacher/add_teacher.html", message = 'Rrror, Please check the fields')
    
    @staticmethod
    def edit_user():
        if request.method == "POST":
            id = request.form.get("edit_student")
            student_info = FirebaseService.getStudent(id)

            if student_info:
                info = {"studentInfo": student_info}
                return render_template("admin/student/edit_student.html", data=info)
            else:
                return "Student not found" 
        else:
            return redirect(url_for("admin")) 
        
    @staticmethod
    def edit_teacher():
        if request.method == "POST":
            value = request.form.get("edit_teacher")
            teacher_info = FirebaseService.getTeacher(value)

            if teacher_info:
                info = {"teacherInfo": teacher_info}
                return render_template("admin/teacher/edit_teacher.html", data=info)
            else:
                return "Student not found" 
        else:
            return redirect(url_for("admin_teacher")) 
        
    @staticmethod
    def save_changes():
        content = request.get_data() # Dạng byte string b'{key:value}
        print(content)
        print('-----------------------')
        dic_data = json.loads(content.decode("utf-8")) # Chuyển về chuỗi thường
        print(dic_data)
        print('-----------------------')
        dic_data = {k: v.strip() for k, v in dic_data.items()} # loại bỏ khoảng trắng thừa
        print(dic_data)
        print('-----------------------')
        email_exist = db.reference("Students").order_by_child("email").equal_to(dic_data['email']).get()
        if email_exist:
            return jsonify({'message': 'Email already exists'}), 400
        dic_data["year"] = int(dic_data["year"])
        dic_data["total_attendance"] = int(dic_data["total_attendance"])
        dic_data["starting_year"] = int(dic_data["starting_year"])

        update_student = db.reference(f"Students")

        update_student.child(dic_data["id"]).update(
            {
                "name": dic_data["name"],
                "dob": dic_data["dob"],
                "address": dic_data["address"],
                "phone": dic_data["phone"],
                "email": dic_data["email"],
                "major": dic_data["major"],
                "starting_year": dic_data["starting_year"],
                "total_attendance": dic_data["total_attendance"],
                "year": dic_data["year"],
                "last_attendance_time": dic_data["last_attendance_time"],
                "content": dic_data["content"],
            }
        )

        return 'Changes saved successfully'
    
    @staticmethod
    def save_changes_teacher():
        content = request.get_data()

        dic_data = json.loads(content.decode("utf-8"))

        dic_data = {k: v.strip() for k, v in dic_data.items()}
        
        email_exist = db.reference("Teachers").order_by_child("email").equal_to(dic_data['email']).get()
        if email_exist:
            return jsonify({'message': 'Email already exists'}), 400
        
        update_teacher = db.reference(f"Teachers")

        update_teacher.child(dic_data["id"]).update(
            {
                "id": dic_data["id"],
                "name": dic_data["name"],
                "dob": dic_data["dob"],
                "address": dic_data["address"],
                "phone": dic_data["phone"],
                "email": dic_data["email"],
            }
        )

        return "Data received successfully!"
    
    @staticmethod
    def delete_user():
        content = request.get_data()
        student_id = json.loads(content.decode("utf-8"))

        delete_student = db.reference(f"Students")
        delete_student.child(student_id).delete()

        # Gọi hàm xóa hình ảnh của sinh viên
        ImageProcessing.delete_image(student_id)
        
        studentIDs, imgList = FirebaseService.add_image_database()

        encodeListKnown = ImageProcessing.findEncodings(imgList)

        encodeListKnownWithIds = [encodeListKnown, studentIDs]

        with open("EncodeFile.p", "wb") as file:
            pickle.dump(encodeListKnownWithIds, file)

        return "Successful"
    
    @staticmethod
    def delete_teacher():
        content = request.get_data()
        teacher_id = json.loads(content.decode("utf-8"))

        delete_teacher = db.reference(f"Teachers")
        delete_teacher.child(teacher_id).delete()

        ImageProcessing.delete_image_teacher(teacher_id)
        
        return "Successful"
