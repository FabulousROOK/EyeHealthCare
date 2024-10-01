import hashlib
from pymongo import MongoClient



class Patient:
    def __init__(self, fullName, email, password):
        self.fullName = fullName
        self.email = email
        self.password = password
    
    @staticmethod
    def db_connection():
        client = MongoClient('mongodb://localhost:27017/')
        db = client['eye_health_care']
        return db['patient']
    
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def get_by_email(email):
        patients = Patient.db_connection()
        return patients.find_one({'email': email})
    
    @staticmethod
    def validate_password(stored_password, provided_password):
        return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()
    
    @staticmethod
    def authenticate(email, password):
        patient_data = Patient.get_by_email(email)
        if patient_data and Patient.validate_password(patient_data['password'], password):
            return patient_data
        return None



    def save(self):
        patients = self.db_connection()
        patients.insert_one(self.__dict__)

    @staticmethod
    def get_all():
        patients = Patient.db_connection()
        return list(patients.find({}))

    @staticmethod
    def get_by_id(patient_id):
        patients = Patient.db_connection()
        return patients.find_one({"_id": patient_id})



class Doctor:
    def __init__(self, fullName, email, specialization, licensenumber, experience, clinicaddress, password):
        self.fullName = fullName
        self.email = email
        specialization = specialization
        licensenumber = licensenumber
        experience = experience
        clinicaddress = clinicaddress
        self.password = password


    
    @staticmethod
    def db_connection():
        client = MongoClient('mongodb://localhost:27017/')
        db = client['eye_health_care']
        return db['doctor']
    
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def get_by_email(email):
        doctors = Doctor.db_connection()
        return doctors.find_one({'email': email})
    
    @staticmethod
    def validate_password(stored_password, provided_password):
        return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()
    
    @staticmethod
    def authenticate(email, password):
        doctor_data = Doctor.get_by_email(email)
        if doctor_data and Doctor.validate_password(doctor_data['password'], password):
            return doctor_data
        return None



    def save(self):
        doctors = self.db_connection()
        doctors.insert_one(self.__dict__)

    @staticmethod
    def get_all():
        doctors = Doctor.db_connection()
        return list(doctors.find({}))

    @staticmethod
    def get_by_id(doctor_id):
        doctors = Doctor.db_connection()
        return doctors.find_one({"_id": doctor_id})
    




class Admin:
    def __init__(self, fullName, email, password):
        self.fullName = fullName
        self.email = email
        self.password = password


    
    @staticmethod
    def db_connection():
        client = MongoClient('mongodb://localhost:27017/')
        db = client['eye_health_care']
        return db['admin']
    
    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def get_by_email(email):
        doctors = Admin.db_connection()
        return doctors.find_one({'email': email})
    
    @staticmethod
    def validate_password(stored_password, provided_password):
        return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()
    
    @staticmethod
    def authenticate(email, password):
        doctor_data = Admin.get_by_email(email)
        if doctor_data and Admin.validate_password(doctor_data['password'], password):
            return doctor_data
        return None



    def save(self):
        doctors = self.db_connection()
        doctors.insert_one(self.__dict__)

    @staticmethod
    def get_all():
        doctors = Admin.db_connection()
        return list(doctors.find({}))

    @staticmethod
    def get_by_id(doctor_id):
        doctors = Admin.db_connection()
        return doctors.find_one({"_id": doctor_id})