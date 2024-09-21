import cv2
import os
import face_recognition
from firebase_admin import storage


class ImageProcessing:

    @staticmethod
    def findID():
        folderPath = "static/Files/Images/students"
        imgPathList = os.listdir(folderPath)
        imgList = []
        studentIDs = []

        for path in imgPathList:
            imgList.append(cv2.imread(os.path.join(folderPath, path)))
            studentIDs.append(os.path.splitext(path)[0])

        return studentIDs, imgList

    @staticmethod
    def findEncodings(images):
        encodeList = []
        
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)

        return encodeList

    @staticmethod
    def delete_image(student_id):
        filepath = f"static/Files/Images/students/{student_id}.jpg"

        os.remove(filepath)

        bucket = storage.bucket()
        blob = bucket.blob(filepath)
        blob.delete()

        return "Successful"

    @staticmethod
    def delete_image_teacher(teacher_id):
        filepath = f"static/Files/Images/teachers/{teacher_id}.jpg"

        os.remove(filepath)

        bucket = storage.bucket()
        blob = bucket.blob(filepath)
        blob.delete()

        return "Successful"
    
    @staticmethod
    def findIDTeacher():
        folderPath = "static/Files/Images/teachers"
        imgPathList = os.listdir(folderPath)
        imgList = []
        teacherIDs = []

        for path in imgPathList:
            imgList.append(cv2.imread(os.path.join(folderPath, path)))
            teacherIDs.append(os.path.splitext(path)[0])

        return teacherIDs, imgList