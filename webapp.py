from flask import Flask, render_template, Response, request
import cv2
import os
import pickle
import face_recognition
import numpy as np
import cvzone
import json
from datetime import datetime
from flask import session, redirect, url_for
from firebase_admin import db
from controllers.student import StudentController
from controllers.teacher import TeacherController
from controllers.Image_processing import ImageProcessing
from controllers.admin import AdminController
from services.firebase_service import FirebaseService

app = Flask(__name__)  # initializing
app.secret_key = 'my_secret_key'

marked_ids_teacher_dict = {}
new_threshold = 0.4


def generate_frame(teacher_id):
    # Background and Different Modes

    # video camera
    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    imgBackground = cv2.imread("static/Files/Resources/background.png")

    folderModePath = "static/Files/Resources/Modes/"
    modePathList = os.listdir(folderModePath)
    imgModeList = []

    for path in modePathList:
        imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

    modeType = 0
    id = -1
    imgStudent = []
    counter = 0

    # encoding loading ---> to identify if the person is in our database or not.... to detect faces that are known or not

    with open("EncodeFile.p", "rb") as file:
        encodeListKnownWithIds = pickle.load(file)
    encodedFaceKnown, studentIDs = encodeListKnownWithIds

    while True:
        success, img = capture.read()

        if not success:
            break
        else:
            imgSmall = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)

            # List Tuple, mỗi tuple chứa tọa độ khuôn mặt detected [( top, right, bottom, left )]
            faceCurrentFrame = face_recognition.face_locations(imgSmall)
            encodeCurrentFrame = face_recognition.face_encodings(
                imgSmall, faceCurrentFrame)

            imgBackground[162: 162 + 480, 55: 55 + 640] = img
            imgBackground[44: 44 + 633, 808: 808 + 414] = imgModeList[modeType]

            if faceCurrentFrame:
                for encodeFace, faceLocation in zip(encodeCurrentFrame, faceCurrentFrame):
                    # trả về danh sách các bô mã mà trong đó lưu true / false
                    matches = face_recognition.compare_faces(
                        encodedFaceKnown, encodeFace, tolerance=new_threshold)  # list true / false
                    # tính khoảng cách xem có gần giống không và trả về khoảng cách đối với các mã trong danh sách
                    # [0.xxx 0.xxx 0.xxx 0.xxx 0.xxx] 
                    faceDistance = face_recognition.face_distance(
                        encodedFaceKnown, encodeFace)
                    # trả về index có khoảng cách nhỏ nhất trong mảng
                    matchIndex = np.argmin(faceDistance) if len(
                        faceDistance) > 0 else -1
                    #print(matches[matchIndex]) true / false
                    if matchIndex != -1 and matches[matchIndex]:
                        if matchIndex < len(studentIDs):
                            id = studentIDs[matchIndex]
                            y1, x2, y2, x1 = faceLocation
                            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                            bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                            imgBackground = cvzone.cornerRect(
                                imgBackground, bbox, rt=0)

                            if counter == 0:
                                cvzone.putTextRect(
                                    imgBackground, "Face Detected", (65, 200), thickness=2)
                                cv2.waitKey(1)
                                counter = 1
                                modeType = 1
                        else:
                            print("Error: Index out of range!")
                    else:
                        # if matchIndex not in studentIDs:  # Kiểm tra xem id có trong danh sách những người đã xóa không
                        #     modeType = 4
                        #     counter = 0
                        #     imgBackground[44: 44 + 633, 808: 808 + 414] = imgModeList[
                        #         modeType
                        #     ]
                        # else:
                        #     cvzone.putTextRect(
                        #         imgBackground, "Face Not Found", (65, 200), thickness=2
                        #     )
                        #     modeType = 4
                        #     counter = 0
                        #     imgBackground[44: 44 + 633, 808: 808 + 414] = imgModeList[
                        #         modeType
                        #     ]
                        if matchIndex not in studentIDs:
                            modeType = 4
                            counter = 0
                            imgBackground[44: 44 + 633, 808: 808 + 414] = imgModeList[
                                modeType
                            ]
                        else:
                            # ID tồn tại trong danh sách ID đã biết nhưng không nhận diện được khuôn mặt
                            modeType = 4
                            counter = 0
                            imgBackground[44: 44 + 633, 808: 808 +
                                          414] = imgModeList[modeType]
                            cvzone.putTextRect(
                                imgBackground, "Face Not Found", (65, 200), thickness=2
                            )
                #print(counter)
                if counter != 0:
                    if counter == 1:
                        studentInfo, imgStudent, secondElapsed = FirebaseService.dataset(
                            id)
                        if secondElapsed > 60:
                            # Cập nhập điểm danh
                            ref = db.reference(f"Students/{id}")
                            studentInfo["total_attendance"] += 1
                            ref.child("total_attendance").set(
                                studentInfo["total_attendance"])
                            ref.child("last_attendance_time").set(
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        else:
                            modeType = 3
                            counter = 0
                            imgBackground[44: 44 + 633, 808: 808 +
                                          414] = imgModeList[modeType]

                            marked_ids_teacher_dict.setdefault(
                                teacher_id, []).append(id)

                            print('--------DS Điểm danh---------')
                            print(marked_ids_teacher_dict)
                            print('--------DS Điểm danh---------')

                    if modeType != 3:
                        if 5 < counter <= 10:
                            modeType = 2

                        imgBackground[44: 44 + 633, 808: 808 +
                                      414] = imgModeList[modeType]

                        if counter <= 5:
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["total_attendance"]),
                                (861, 125),
                                cv2.FONT_HERSHEY_COMPLEX,
                                1,
                                (255, 255, 255),
                                1,
                            )
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["major"]),
                                (1006, 550),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.5,
                                (255, 255, 255),
                                1,
                            )
                            cv2.putText(
                                imgBackground,
                                str(id),
                                (1006, 493),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.5,
                                (255, 255, 255),
                                1,
                            )
                            # cv2.putText(
                            #    imgBackground,
                            #    str(studentInfo["standing"]),
                            #    (910, 625),
                            #    cv2.FONT_HERSHEY_COMPLEX,
                            #    0.6,
                            #    (100, 100, 100),
                            #    1,
                            # )
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["year"]),
                                (1025, 625),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.6,
                                (100, 100, 100),
                                1,
                            )
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["starting_year"]),
                                (1125, 625),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.6,
                                (100, 100, 100),
                                1,
                            )

                            (w, h), _ = cv2.getTextSize(
                                str(studentInfo["name"]
                                    ), cv2.FONT_HERSHEY_COMPLEX, 1, 1
                            )

                            offset = (414 - w) // 2
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["name"]),
                                (808 + offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX,
                                1,
                                (50, 50, 50),
                                1,
                            )

                            imgStudentResize = cv2.resize(
                                imgStudent, (216, 216))

                            imgBackground[
                                175: 175 + 216, 909: 909 + 216
                            ] = imgStudentResize

                        counter += 1

                        if counter >= 10:
                            counter = 0
                            modeType = 0
                            studentInfo = []
                            imgStudent = []
                            imgBackground[44: 44 + 633, 808: 808 + 414] = imgModeList[
                                modeType
                            ]

            else:
                modeType = 0
                counter = 0
            # chuyển đổi imgbackground thành mảng byte băng cách use định dạng jpeg
            # ret là biến boolean , frame -> chưa dữ liệu byte của hình ảnh được mã hóa
            ret, buffer = cv2.imencode(".jpeg", imgBackground)
            # chuyển đổi mảng byte 'buffer' thành thành 1 chuỗi bytes
            frame = buffer.tobytes()
        # dùng yield trả về 1 generator, mỗi lần lặp trả về khối dữ liệu theo chuẩn http multipart
        # b"--frame\r\n" : Đánh dấu bắt đầu của 1 khối dữ liệu, 
        # b"Content-Type: image/jpeg \r\n\r\n": định dạng nội dung dữ liệu là hình ảnh,
        #  + frame + : dữ liệu thực của ảnh được gắn vào
        # b"\r\n" : Đánh dấu kết thúc của 1 khối dữ liệu
        yield (b"--frame\r\n" b"Content-Type: image/jpeg \r\n\r\n" + frame + b"\r\n")


#########################################################################################################################

##################################################### --index--########################################################

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video")
def video():
    if 'teacher_id' in session:
        teacher_id = session['teacher_id']
        return Response(generate_frame(teacher_id), mimetype="multipart/x-mixed-replace; boundary=frame")
    else:
        return redirect(url_for('teacher_login'))


##################################################### --index--########################################################

##################################################### --Student--########################################################

@app.route("/student_login", methods=["GET", "POST"])
def student_login():
    return StudentController.login()


@app.route("/student/<data>/<title>")
def student(data, title=None):
    if 'student_id' in session:
        return StudentController.student(data, title)
    else:
        return redirect(url_for('student_login'))


@app.route("/student_logout", methods=["GET", "POST"])
def student_logout():
    session.pop('student_id', None)
    return redirect(url_for('student_login'))

##################################################### --Student--########################################################

##################################################### --Teacher--########################################################

@app.route("/teacher_login", methods=["GET", "POST"])
def teacher_login():
    return TeacherController.login()


@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    if 'teacher_id' in session:
        return TeacherController.teacher()
    else:
        return redirect(url_for('teacher_login'))


@app.route("/teacher/teacher_attendance_list", methods=["GET", "POST"])
def teacher_attendance_list():
    if 'teacher_id' in session:
        teacher_id = session['teacher_id']
        return TeacherController.teacher_attendance_list(marked_ids_teacher_dict.get(teacher_id, []))
    else:
        return redirect(url_for('teacher_login'))


@app.route("/teacher_logout")
def teacher_logout():
    session.pop('teacher_id', None)
    return redirect(url_for('teacher_login'))

##################################################### --Teacher--########################################################

##################################################### --Admin--########################################################

##################################################### --Admin ( Login, Logout )--########################################################


@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    return AdminController.login()


@app.route("/admin_logout", methods=["GET", "POST"])
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))


##################################################### --Admin ( Login, Logout )--########################################################

##################################################### --Admin ( students, teachers )--########################################################


@app.route("/admin")
def admin():
    if 'admin_id' in session:
        return AdminController.admin()
    else:
        return redirect(url_for('admin_login'))


@app.route("/admin/teachers")
def admin_teacher():
    if 'admin_id' in session:
        return AdminController.admin_teacher()
    else:
        return redirect(url_for('admin_login'))
    

##################################################### --Admin ( students, teachers )--########################################################

##################################################### --Admin ( Add students, teachers )--########################################################


@app.route("/admin/add_user", methods=["GET", "POST"])
def add_user():
    if 'admin_id' in session:
        return AdminController.add_user()
    else:
        return redirect(url_for('admin_login'))


@app.route("/admin/add_teacher", methods=["GET", "POST"])
def add_teacher():
    if 'admin_id' in session:
        return AdminController.add_teacher()
    else:
        return redirect(url_for('admin_login'))
    
    
##################################################### --Admin ( Add students, teachers )--########################################################


##################################################### --Admin ( Edit students, teachers )--########################################################

@app.route("/admin/edit_user", methods=["POST", "GET"])
def edit_user():
    if 'admin_id' in session:
        return AdminController.edit_user()
    else:
        return redirect(url_for('admin_login'))


@app.route("/admin/edit_teacher", methods=["POST", "GET"])
def edit_teacher():
    if 'admin_id' in session:
        return AdminController.edit_teacher()
    else:
        return redirect(url_for('admin_login'))

##################################################### --Admin ( Edit students, teachers )--########################################################

##################################################### --Admin ( Update students, teachers )--########################################################


@app.route("/admin/save_changes", methods=["POST", "GET"])
def save_changes():
    if 'admin_id' in session:
        return AdminController.save_changes()
    else:
        return redirect(url_for('admin_login'))


@app.route("/admin/save_changes_teacher", methods=["POST", "GET"])
def save_changes_teacher():
    if 'admin_id' in session:
        return AdminController.save_changes_teacher()
    else:
        return redirect(url_for('admin_login'))
    
    
##################################################### --Admin ( Update students, teachers )--########################################################

##################################################### --Admin ( Delete students, teachers )--########################################################


@app.route("/admin/delete_user", methods=["POST", "GET"])
def delete_user():
    if 'admin_id' in session:
        return AdminController.delete_user()
    else:
        return redirect(url_for('admin_login'))


@app.route("/admin/delete_teacher", methods=["POST", "GET"])
def delete_teacher():
    if 'admin_id' in session:
        return AdminController.delete_teacher()
    else:
        return redirect(url_for('admin_login'))
    
##################################################### --Admin ( Delete students, teachers )--########################################################

##################################################### --Admin--########################################################


if __name__ == "__main__":
    app.run(debug=True, port=3000)
