import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import numpy as np
import cv2
import os
from datetime import datetime

# database credentials
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://face-recognition-d4d9b-default-rtdb.firebaseio.com/',
    'storageBucket': 'face-recognition-d4d9b.appspot.com',
})

class FirebaseService:
    
    @staticmethod
    def getStudent(id):
        studentInfo = db.reference(f"Students/{id}").get()
        return studentInfo
    
    @staticmethod
    def getTeacher(id):
        teacherInfo = db.reference(f"Teachers/{id}").get()
        return teacherInfo
    
    @staticmethod
    def getAdmin(id):
        adminInfo = db.reference(f"Admins/{id}").get()
        return adminInfo
    
    @staticmethod
    def dataset(id):
        studentInfo =  db.reference(f"Students/{id}").get()
        bucket = storage.bucket()
        blob =  bucket.get_blob(f"static/Files/Images/students/{id}.jpg")
        array =  np.frombuffer(blob.download_as_string(), np.uint8)
        imgStudent =  cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
        datetimeObject = datetime.strptime(
            studentInfo["last_attendance_time"], "%Y-%m-%d %H:%M:%S"
        )
        secondElapsed = (datetime.now() - datetimeObject).total_seconds()
        return studentInfo, imgStudent, secondElapsed
    
    @staticmethod
    def add_image_database():
        folderPath = "static/Files/Images/students"
        imgPathList = os.listdir(folderPath)
        imgList = []
        studentIDs = []

        for path in imgPathList:
            imgList.append(cv2.imread(os.path.join(folderPath, path)))
            studentIDs.append(os.path.splitext(path)[0])

            fileName = f"{folderPath}/{path}"
            bucket = storage.bucket()
            blob = bucket.blob(fileName)
            blob.upload_from_filename(fileName)

        return studentIDs, imgList
    
    @staticmethod
    def add_image_database_teacher():
        folderPath = "static/Files/Images/teachers"
        imgPathList = os.listdir(folderPath)
        imgList = []
        teacherIDs = []

        for path in imgPathList:
            imgList.append(cv2.imread(os.path.join(folderPath, path)))
            teacherIDs.append(os.path.splitext(path)[0])

            fileName = f"{folderPath}/{path}"
            bucket = storage.bucket()
            blob = bucket.blob(fileName)
            blob.upload_from_filename(fileName)

        return teacherIDs, imgList