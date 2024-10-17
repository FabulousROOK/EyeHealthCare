import hashlib
from pymongo import MongoClient
from bson.objectid import ObjectId



class Patient:
    def __init__(self, fullName, email, password=None, profilepicturepath=None, status='Active'):
        self.fullName = fullName
        self.email = email
        self.password = password
        self.profilepicturepath = profilepicturepath
        self.status = status
    
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
    

    def update(patient_id, udate_date):
        patient = Patient.db_connection()
        patient.update_one({'_id': patient_id}, {'$set': udate_date})


    @staticmethod
    def get_by_id(patient_id):
        patients = Patient.db_connection()
        return patients.find_one({"_id": patient_id})
    
    @staticmethod
    def delete_patient_profile(patient_id):
        doctor = Patient.db_connection()
        doctor.delete_one({'_id': patient_id})



class Doctor:
    def __init__(self, fullName, email, specialization, licensenumber, experience, clinicaddress, password=None, profilepicturepath=None, status='Pending'):
        self.fullName = fullName
        self.email = email
        self.specialization = specialization
        self.licensenumber = licensenumber
        self.experience = experience
        self.clinicaddress = clinicaddress
        self.password = password
        self.profilepicturepath = profilepicturepath
        self.status = status


    
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

    def update(doctor_id, update_data):
        doctor = Doctor.db_connection()
        doctor.update_one({'_id': doctor_id}, {'$set': update_data})
    

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
    
    @staticmethod
    def delete_doctor_profile(slot_id):
        doctor = Doctor.db_connection()
        doctor.delete_one({'_id': slot_id})

    
    def get_appointments(doctor_id):
        appointments = Appointment.db_connection()
        return list(appointments.find({"doctor_id": doctor_id}))





class Appointment:
    def __init__(self, doctor_id=None, name=None, type=None, date=None, time=None, locationName=None, max_bookings=None, existing_appointment=None):
        if existing_appointment:
            self.doctor_id = existing_appointment['doctor_id'] if doctor_id is None else doctor_id
            self.name = name or existing_appointment['name']
            self.type = type or existing_appointment['type']
            self.date = date or existing_appointment['date']
            self.time = time or existing_appointment['time']
            self.locationName = locationName or existing_appointment['locationName']
            self.max_bookings = max_bookings or existing_appointment['max_bookings']
            self.bookings = existing_appointment.get('bookings', [])

        else:
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
    def get_by_id(slot_id):
        appointments = Appointment.db_connection()
        return appointments.find_one({'_id': slot_id})
    
    def update_appointment_slot(self, slot_id):
        appointments = Appointment.db_connection()
        
        update_data = {k: v for k, v in self.__dict__.items() if k != '_id'}
        appointments.update_one({'_id': ObjectId(slot_id)}, {'$set': update_data})
    
    @staticmethod
    def delete_appointment_slot(slot_id):
        appointment = Appointment.db_connection()
        appointment.delete_one({'_id': slot_id})


    @staticmethod
    def booking_appointment(appointment_id, patient_id, patient_name, date_time):
        appointments = Appointment.db_connection()
        appointment = appointments.find_one({"_id": ObjectId(appointment_id)})

        if not appointment:
            return None, "error_appointment_not_found"

        # Check if the patient has already booked the appointment
        for booking in appointment['bookings']:
            if str(booking['patient_id']) == str(patient_id) and booking['status'] == 'Active':
                return None, "error_already_booked"
            
            if str(booking['patient_id']) == str(patient_id) and booking['status'] == 'Canceled':
                booking_number = int(booking['booking_number'])
                result = appointments.update_one(
                    {
                        '_id': ObjectId(appointment_id), 
                        'bookings.patient_id': ObjectId(patient_id), 
                        'bookings.booking_number': booking_number
                    }, 
                    {
                        '$set': {'bookings.$.status': 'Active'}
                    } 
                )


                print(f"Modified Count: {result.modified_count}")
                return booking_number, "Booking restored successfully"

        

        if appointment and len(appointment['bookings']) < appointment['max_bookings']:
            booking_number = len(appointment['bookings']) + 1
            
            appointments.update_one(
                {"_id": ObjectId(appointment_id)},
                {"$push": 
                 {"bookings": {"patient_id": ObjectId(patient_id), "booking_number": booking_number, "patient_name": patient_name, "date_time": date_time, "status": 'Active'}}}
            )

            return booking_number, "Booking successful"
    
        return None, "error_slot_full"
    

    def get_bookings(patient_id):
        appointments = Appointment.db_connection()
        doctors = Doctor.db_connection()
        appointments_with_patient_booking = appointments.find({'bookings.patient_id': ObjectId(patient_id)})

        patient_bookings = []
        for appointment in appointments_with_patient_booking:
            doctor = doctors.find_one({'_id': ObjectId(appointment['doctor_id'])})
            # Loop through all bookings in the appointment to find the ones matching the patient_id
            for booking in appointment['bookings']:
                if booking['patient_id'] == ObjectId(patient_id) and booking['status'] == 'Active':
                    booking_info = {
                        "appointment_id": str(appointment['_id']),
                        "appointment_name": appointment['name'],
                        "appointment_date": appointment['date'],
                        "appointment_time": appointment['time'],
                        "location": appointment['locationName'],
                        "doctor": doctor['fullName'],
                        "booking_number": booking['booking_number'],
                        "patient_name": booking['patient_name']
                    }
                    patient_bookings.append(booking_info)

        return patient_bookings
    

    def cancel_bookings(patient_id, appointment_id, booking_number):
        appointments = Appointment.db_connection()

        result = appointments.update_one(
            {
                '_id': ObjectId(appointment_id), 
                'bookings.patient_id': ObjectId(patient_id), 
                'bookings.booking_number': booking_number
            }, 
            {
                '$set': {'bookings.$.status': 'Canceled'}
            } 
        )


        return result





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
    


class MLmodels:
    def __init__(self, name, path, status='Inactive'):
        self.name = name
        self.path = path
        self.status = status
    
    @staticmethod
    def db_connection():
        client = MongoClient('mongodb://localhost:27017/')
        db = client['eye_health_care']
        return db['mlmodels']
    
    def save(self):
        ml_models = self.db_connection()
        ml_models.insert_one(self.__dict__)
        
    @staticmethod
    def get_all():
        ml_models = MLmodels.db_connection()
        return list(ml_models.find({}))
    
    def update(ml_model_id, update_data):
        ml_models = MLmodels.db_connection()
        ml_models.update_one({'_id': ml_model_id}, {'$set': update_data})
    
    @staticmethod
    def get_by_id(ml_model_id):
        ml_models = MLmodels.db_connection()
        return ml_models.find_one({'_id': ml_model_id})
    
    @staticmethod
    def delete_model(ml_model_id):
        ml_models = MLmodels.db_connection()
        ml_models.delete_one({'_id': ml_model_id})