import hashlib
from pymongo import MongoClient
from bson.objectid import ObjectId



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
        self.specialization = specialization
        self.licensenumber = licensenumber
        self.experience = experience
        self.clinicaddress = clinicaddress
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


    def save_doctor(self):
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
    

    def create_appointment(self, name, type, date, time, locationName, max_bookings):

        if self._id is None:
            raise ValueError("Doctor must be saved to the database before creating an appointment.")
        
        appointment = Appointment(
            doctor_id=self._id, 
            name=name,
            type=type,
            date=date,
            time=time,
            locationName=locationName,
            max_bookings=max_bookings
        )

        appointment.save_appointments()
    
    def get_appointments(doctor_id):
        appointments = Appointment.db_connection()
        return list(appointments.find({"doctor_id": doctor_id}))





class Appointment:
    def __init__(self, doctor_id, name, type, date, time, locationName, max_bookings):
        self.doctor_id = doctor_id
        self.name = name
        self.type = type
        self.date = date
        self.time = time
        self.locationName = locationName
        self.max_bookings = max_bookings
        self.bookings = []

    @staticmethod
    def db_connection():
        client = MongoClient('mongodb://localhost:27017/')
        db = client['eye_health_care']
        return db['appointment']
    

    def save_appointments(self):
        appointment = self.db_connection()
        appointment.insert_one(self.__dict__)

    @staticmethod
    def get_all():
        appoinments = Appointment.db_connection()
        return list(appoinments.find({}))

    @staticmethod
    def booking_appointment(appointment_id, patient_id):
        appointments = Appointment.db_connection()
        appointment = appointments.find_one({"_id": ObjectId(appointment_id)})

        if appointment and len(appointment['bookings']) < appointment['max_bookings']:
            booking_number = len(appointment['bookings']) + 1
            
            appointments.update_one(
                {"_id": ObjectId(appointment_id)},
                {"$push": {"bookings": {"patient_id": ObjectId(patient_id), "booking_number": booking_number}}}
            )

            return booking_number
        return None





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