from flask import Flask, render_template, url_for, redirect, request, session, flash, make_response, jsonify
from models import Patient, Doctor, Admin, Appointment, MLmodels
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import math

from bson.objectid import ObjectId


app = Flask(__name__)
app.secret_key = 'qwe123'

@app.after_request
def prevent_caching(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.pop('patient_id', None)
    session.pop('doctor_id', None)
    session.pop('admin_id', None)
    session.clear()

    return redirect(url_for('index'))


@app.route('/login-doctor', methods = ['GET','POST'])
def doctor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        doctor = Doctor.authenticate(email, password)

        if doctor:
            session['doctor_id'] = str(doctor['_id'])  # Store user ID in session
            session['doctor_email'] = doctor['email']
            session['doctor_status'] = doctor['status']
            return redirect(url_for('doctor_home'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('doctor-login.html')


@app.route('/doctor-register', methods = ['GET', 'POST'])
def doctor_register():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        specialization = request.form['specialization']
        licensenumber = request.form['licensenumber']
        experience = request.form['experience']
        clinicaddress = request.form['clinicaddress']
        confirmpassword = request.form['confirmpassword']
        hashed_password = Patient.hash_password(confirmpassword)

        doctor = Doctor(fullname, email, specialization, licensenumber, experience, clinicaddress, hashed_password)
        doctor.save_doctor()
        return redirect(url_for('doctor_login'))

    return render_template('doctor-register.html')




@app.route('/doctor-home')
def doctor_home():
    if 'doctor_id' in session:
        doctor_id = session['doctor_id']
        appointments = Doctor.get_appointments(doctor_id)
        for appointment in appointments:
            appointment['date'] = datetime.fromisoformat(appointment['date'])
            appointment['status'] = 'Ended' if appointment['date'] < datetime.now() else 'Upcoming'

            appointment['total_bookings'] = len(appointment['bookings'])
            appointment['active_bookings'] = sum(1 for booking in appointment['bookings'] if booking['status'] == 'Active')

        page = request.args.get('page', 1, type=int)
        per_page = 5
        total_items = len(appointments)
        total_pages = math.ceil(total_items / per_page)

        start = (page - 1)*per_page
        end = start + per_page
        paginated_appointments = appointments[start:end]

        return render_template('doctor/doctor-home.html', appointments=paginated_appointments, page=page, total_pages=total_pages )
    return redirect(url_for('index'))

@app.route('/appointment-slots-fragment')
def view_appointment_slots():
    if 'doctor_id' in session:

        doctor_id = session['doctor_id']
        appointments = Doctor.get_appointments(doctor_id)
        for appointment in appointments:
            appointment['date'] = datetime.fromisoformat(appointment['date'])
            appointment['status'] = 'Ended' if appointment['date'] < datetime.now() else 'Upcoming'

            appointment['total_bookings'] = len(appointment['bookings'])
            appointment['active_bookings'] = sum(1 for booking in appointment['bookings'] if booking['status'] == 'Active')

        page = request.args.get('page', 1, type=int)
        per_page = 5
        total_items = len(appointments)
        total_pages = math.ceil(total_items / per_page)

        start = (page - 1)*per_page
        end = start + per_page
        paginated_appointments = appointments[start:end]
        
        return render_template('components/doctor/doctor-view-appointments.html', appointments=paginated_appointments, page=page, total_pages=total_pages)
    
    return '', 403  # Return 403 if unauthorized


@app.route('/view-edit-appointment-slots/<slot_id>', methods=['GET'])
def view_edit_appointment_slots(slot_id):
    appointment = Appointment.get_by_id(ObjectId(slot_id))

    if appointment:
        session['appointment_slot_id'] = slot_id
        appointment['_id'] = str(appointment['_id'])
        return jsonify(appointment)
    return jsonify({'error': 'Appointment not found'})


@app.route('/create-appointment-slot', methods = ['GET', 'POST'])
def create_appointment_slot():
    if 'doctor_id' in session and 'doctor_status' in session:
        if session['doctor_status'] == 'Approved':
            if request.method == 'POST':
                name = request.form['appointmentSlotName']
                type = request.form['appointmentType']
                date = request.form['date']
                time = request.form['time']
                locationName = request.form['location']
                max_bookings = int(request.form['maxBookings'])
                doctor_id = session['doctor_id']

                appointmentSlot = Appointment(doctor_id, name, type, date, time, locationName, max_bookings)
                appointmentSlot.save_appointments()

                return jsonify({'success': 'Appointment slot added successfully'})
        return jsonify({'error': 'Cannot Create as the Profile is not yet approved'})
    return jsonify({'error': 'Appointment slot addition failed'})


@app.route('/update-edit-appointment-slots', methods = ['GET', 'POST'])
def update_edit_appointment_slots():
    slot_id = session.get('appointment_slot_id')
    existing_appointment  = Appointment.get_by_id(ObjectId(slot_id))

    if request.method == 'POST':
        appointmentSlotName = request.form['editAppointmentSlotName']
        appointmentType = request.form['editAppointmentType']
        date = request.form['editDate']
        time = request.form['editTime']
        locationName = request.form['editLocation']
        max_bookings = int(request.form['editMaxBookings'])

        appointment_slot_instance = Appointment(
            doctor_id = existing_appointment['doctor_id'], 
            name = appointmentSlotName, 
            type = appointmentType, 
            date = date, 
            time = time, 
            locationName = locationName, 
            max_bookings = max_bookings,
            existing_appointment=existing_appointment
        )


        appointment_slot_instance.update_appointment_slot(slot_id)
        session.pop('appointment_slot_id', None)
        

        return jsonify({'success': 'Appointment Updated'})
    
    return jsonify({'error': 'Appointment not Updated'})

@app.route('/delete-appointment-slot', methods = ['GET', 'POST'])
def delete_appointment_slot():
    data = request.get_json()
    slot_id = data.get('slot_id')

    if slot_id:
        Appointment.delete_appointment_slot(ObjectId(slot_id))
        return jsonify({'success': 'Appointment slot deleted'})
    return jsonify({'error': 'No appointment slot ID provided'})


@app.route('/doctor-ml-model')
def doctor_ml_model():
    if 'doctor_id' in session:
        return render_template('doctor/doctor-ml-model.html')
    return redirect(url_for('index'))


@app.route('/doctor-profile')
def doctor_profile():
    if 'doctor_id' in session:
        doctor_id = session['doctor_id']
        doctor = Doctor.get_by_id(ObjectId(doctor_id))
        if doctor:
            return render_template('doctor/doctor-profile.html', doctor=doctor)
        else:
            return redirect(url_for('index'))
    return redirect(url_for('index'))




UPLOAD_FOLDER_DOCTOR = 'static/images/doctor/profile'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER_DOCTOR'] = UPLOAD_FOLDER_DOCTOR

def allowed_file(filename):
    return '.'in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/doctor-update-profile', methods=['GET','POST'])
def update_doctor_profile():
    if 'doctor_id' in session:
        doctor_id = session['doctor_id']
        doctor = Doctor.get_by_id(ObjectId(doctor_id))

        if doctor:
            if request.method == 'POST':

                fullName = request.form['fullname']
                email = request.form['email']
                specialization = request.form['specialization']
                licensenumber = request.form['licensenumber']
                experience = request.form['experience']
                clinicaddress = request.form['clinicaddress']

                update_data = {
                    'fullName': fullName,
                    'email': email,
                    'specialization': specialization,
                    'licensenumber': licensenumber,
                    'experience': experience,
                    'clinicaddress': clinicaddress
                }



                if 'profile_picture' in request.files:
                    file = request.files['profile_picture']
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER_DOCTOR'], filename)
                        file.save(file_path)
                        update_data['profilepicturepath'] = file_path  # Save path in update_data
                else: 
                    print("No Data")
                        

                # Update doctor details in the database
                Doctor.update(ObjectId(doctor_id), update_data)

                return jsonify({'success': "Profile Updated"})
        else:
            return redirect(url_for('index'))
    
    
    


@app.route('/patient-home')
def patient_home():
    if 'patient_id' in session:
        patient_id = session['patient_id']
        bookings = Appointment.get_bookings(ObjectId(patient_id))
        return render_template('patient/patient-home.html', patient_id = patient_id, bookings = bookings)
    return redirect(url_for('index'))


@app.route('/patient-profile')
def patient_profile():
    if 'patient_id' in session:
        patient_id = session['patient_id']
        patient = Patient.get_by_id(ObjectId(patient_id))
        if patient:
            return render_template('patient/patient-profile.html', patient=patient)
        else:
            return redirect(url_for('index'))
    return redirect(url_for('index'))



UPLOAD_FOLDER_PATIENT = 'static/images/patient/profile'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER_PATIENT'] = UPLOAD_FOLDER_PATIENT

def allowed_file(filename):
    return '.'in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/patient-update-profile', methods=['GET','POST'])
def update_patient_profile():
    if 'patient_id' in session:
        patient_id = session['patient_id']
        patient = Patient.get_by_id(ObjectId(patient_id))

        if patient:
            if request.method == 'POST':

                fullName = request.form['fullname']
                email = request.form['email']

                update_data = {
                    'fullName': fullName,
                    'email': email,
                }



                if 'profile_picture' in request.files:
                    file = request.files['profile_picture']
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER_PATIENT'], filename)
                        file.save(file_path)
                        update_data['profilepicturepath'] = file_path  # Save path in update_data
                else: 
                    print("No Data")
                        

                # Update patient details in the database
                Patient.update(ObjectId(patient_id), update_data)

                return jsonify({'success': "Profile Updated"})
        else:
            return redirect(url_for('index'))
    

@app.route('/patient-home-doctor-cards')
def patient_home_doctor_cards():
    doctor_profiles = Doctor.get_all()
    doctor_active_profiles = [profile for profile in doctor_profiles if profile.get('status')=='Approved']

    page = request.args.get('page', 1, type=int)
    per_page = 4
    total_items = len(doctor_active_profiles)
    total_pages = math.ceil(total_items / per_page)

    start = (page - 1)*per_page
    end = start + per_page
    paginated_doctor_active_profiles = doctor_active_profiles[start:end]
        
    return render_template('components/patient/patient-home-doctor-cards.html', doctor_active_profiles=paginated_doctor_active_profiles, page=page, total_pages=total_pages)


@app.route('/patient-view-doctor-profile', methods = ['GET', 'POST'])
def patient_view_doctor_profile():
    doctor_id = request.form['doctor_id']
    print('doc ID :  ', doctor_id)
    doctor_profile = Doctor.get_by_id(ObjectId(doctor_id))
    appointment_slots_all = Appointment.get_all()

    current_date = datetime.now().date()
    appointment_active_slots = [slot for slot in appointment_slots_all if datetime.strptime(slot.get('date'), '%Y-%m-%d').date() >= current_date and slot.get('doctor_id') == doctor_id]

    for appointment_active_slot in appointment_active_slots:
            appointment_active_slot['date'] = datetime.fromisoformat(appointment_active_slot['date'])
    
    return render_template('patient/patient-appointment-booking.html', appointment_active_slots=appointment_active_slots, doctor_profile=doctor_profile)


@app.route('/patient-book-appointments', methods=['GET', 'POST'])
def patient_book_appointments():
    if 'patient_id' in session:
        data = request.get_json()
        slot_id = data.get('slot_id')
        patient_id = session['patient_id']
        patient_profile = Patient.get_by_id(ObjectId(patient_id))
        patient_name = patient_profile['fullName']
        date_time = datetime.now()


        result = Appointment.booking_appointment(ObjectId(slot_id), ObjectId(patient_id), patient_name, date_time)

        # Ensure result is unpacked correctly
        if isinstance(result, tuple) and len(result) == 2:  # Check if result is a tuple with 2 elements
            booking_number, message = result
            
            if booking_number is not None:  # Booking was successful
                return jsonify({"message": message, "booking_number": booking_number}), 200
            else:  # Booking failed
                if message == "error_appointment_not_found":
                    return jsonify({"message": "Appointment slot not found."}), 404
                elif message == "error_already_booked":
                    return jsonify({"message": "You have already booked this appointment."}), 400
                elif message == "error_slot_full":
                    return jsonify({"message": "The slot is full."}), 400
                else:
                    return jsonify({"message": message}), 400  # Generic error message
        else:
            return jsonify({"message": "An unexpected error occurred."}), 500


    else:
        return redirect(url_for('index'))
    

# @app.route('/patient-view-appoinments')
# def patient_view_appoinments():
#     if 'patient_id' in session:
#         patient_id = session['patient_id']
#         bookings = Appointment.get_bookings(ObjectId(patient_id))

#         print('bookings',bookings)

@app.route('/patient-cancel-appointment', methods = ['POST'])
def patient_cancel_appointment():
    if 'patient_id' in session:
        patient_id = session['patient_id']
        appointment_id = request.form.get('appointment_id')
        booking_number = int(request.form.get('booking_number'))

        result = Appointment.cancel_bookings(ObjectId(patient_id), ObjectId(appointment_id), booking_number)

        if result.modified_count > 0:
            return jsonify({'success': "Appointment Cancelled"})
        else:
            return jsonify({'error': "Cancellation failed, booking not found"})

    else:
        return redirect(url_for('index'))

    


@app.route('/admin-login', methods = ['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin = Admin.authenticate(email, password)

        if admin:
            session['admin_id'] = str(admin['_id'])  # Store user ID in session
            session['admin_email'] = admin['email']
            return redirect(url_for('admin_home'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('admin/admin-login.html')


@app.route('/admin-create', methods = ['GET', 'POST'])
def admin_create():
    if request.method == 'POST':
        fullName = request.form['fullname']
        email = request.form['email']
        password = request.form['confirm-password']
        hashed_password = Admin.hash_password(password)

        admin = Admin(fullName, email, hashed_password)
        admin.save()
        return redirect(url_for('admin_login'))
    return render_template('admin/admin-create.html')




@app.route('/admin-home')
def admin_home():
    if 'admin_id' in session:
        return render_template('admin/admin-home.html')
    return redirect(url_for('index'))

@app.route('/admin-home-main-cards')
def admin_home_main_cards():
    if 'admin_id' in session:
        doctor_profile_count = len(Doctor.get_all())
        patient_profile_count = len(Patient.get_all())
        ml_models_count = len(MLmodels.get_all())

        return render_template('components/admin/admin-main-dashboard-cards.html', doctor_profile_count=doctor_profile_count, patient_profile_count=patient_profile_count, ml_models_count=ml_models_count )
    return redirect(url_for('index'))


UPLOAD_FOLDER_MODELS = 'static/models'
ALLOWED_EXTENSIONS_MODELS = {'pkl', 'h5', 'onnx', 'joblib', 'json'}

app.config['UPLOAD_FOLDER_MODELS'] = UPLOAD_FOLDER_MODELS

def allowed_file_models(filename):
    return '.'in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_MODELS


@app.route('/admin-create-models', methods = ['GET', 'POST'])
def create_models():
    if request.method == 'POST':
        name = request.form['name']
        
        if 'model_file_input' in request.files:
            file = request.files['model_file_input']
            if file and allowed_file_models(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER_MODELS'], filename)
                file.save(file_path)
                model_file_path = file_path
                # print("file", model_file_path)
            else: 
                print("No Data")

        model = MLmodels(name, model_file_path)
        
        model.save()

        return jsonify({'success': 'ML Model added successfully'})
    return jsonify({'error': 'ML Model addition failed'})


@app.route('/admin-view-models')
def admin_view_models():
    if 'admin_id' in session:
        ml_models = MLmodels.get_all()
        

        page = request.args.get('page', 1, type=int)
        per_page = 4
        total_items = len(ml_models)
        total_pages = math.ceil(total_items / per_page)

        start = (page - 1)*per_page
        end = start + per_page
        paginated_ml_models = ml_models[start:end]
        
        return render_template('components/admin/admin-view-models.html', ml_models=paginated_ml_models, page=page, total_pages=total_pages)
    
    return redirect(url_for('index'))


@app.route('/admin-ml-model-status-update/<ml_model_id>', methods = ['GET', 'POST'])
def admin_ml_model_status_update(ml_model_id):
    if 'admin_id' in session:
        if 'status' in request.form and request.form['status'] == 'Active' or request.form['status'] == 'Inactive' :
            ml_model = MLmodels.get_by_id(ObjectId(ml_model_id))
            all_ml_model = MLmodels.get_all()

            active_ml_models = [model for model in all_ml_model if model.get('status') == 'Active']
            status = request.form['status']

            if not active_ml_models:

                if ml_model:
                    
                    update_data = {
                        'status': status
                    }

                    MLmodels.update(ObjectId(ml_model_id), update_data)

                    return jsonify({'success': "Model Updated"})
                
                return jsonify({'error': "No Model Found"})
            
            elif ml_model and status == 'Inactive':
                
                update_data = {
                    'status': status
                }

                MLmodels.update(ObjectId(ml_model_id), update_data)

                return jsonify({'success': "Model Updated"})
            
            return jsonify({'warning': "A model is already Active"})
        
        return jsonify({'error': "Form Data Not Found"})
    
    return redirect(url_for('index'))




@app.route('/admin-doctor-management')
def admin_doctor_management():
    if 'admin_id' in session:

        return render_template('admin/admin-doctor-management.html')
    
    return redirect(url_for('index'))


@app.route('/admin-get-all-doctors')
def admin_get_all_doctor():
    if 'admin_id' in session:

        doctor_profiles = Doctor.get_all()
        

        page = request.args.get('page', 1, type=int)
        per_page = 5
        total_items = len(doctor_profiles)
        total_pages = math.ceil(total_items / per_page)

        start = (page - 1)*per_page
        end = start + per_page
        paginated_doctor_profiles = doctor_profiles[start:end]
        
        return render_template('components/admin/admin-view-doctors.html', doctor_profiles=paginated_doctor_profiles, page=page, total_pages=total_pages)
    
    return redirect(url_for('index'))


@app.route('/view-doctor-profile/<doctor_id>', methods=['GET'])
def view_doctor_profile(doctor_id):
    doctor_profile = Doctor.get_by_id(ObjectId(doctor_id))

    if doctor_profile:
        doctor_profile['_id'] = str(doctor_profile['_id'])
        return jsonify(doctor_profile)
    return jsonify({'error': 'Doctor profile not found'})


@app.route('/admin-doctor-profile-status-update/<doctor_id>', methods=['GET','POST'])
def admin_doctor_profile_status_update(doctor_id):
    if 'admin_id' in session:
        doctor = Doctor.get_by_id(ObjectId(doctor_id))

        if doctor:
            if request.method == 'POST':

                status = request.form['status']

                update_data = {
                    'status': status
                }
                        

                # Update doctor details in the database
                Doctor.update(ObjectId(doctor_id), update_data)

                return jsonify({'success': "Profile Updated"})
        else:
            return redirect(url_for('index'))


@app.route('/admin-delete-doctor-profile', methods = ['GET', 'POST'])
def admin_delete_doctor_profile():
    data = request.get_json()
    doctor_id = data.get('doctor_id')

    if doctor_id:
        Doctor.delete_doctor_profile(ObjectId(doctor_id))
        return jsonify({'success': 'Profile deleted'})
    return jsonify({'error': 'No profile ID provided'})


@app.route('/admin-patient-management')
def admin_patient_management():
    if 'admin_id' in session:
        return render_template('admin/admin-patient-management.html')
    return redirect(url_for('index'))


@app.route('/admin-get-all-patients')
def admin_get_all_patients():
    if 'admin_id' in session:

        patient_profiles = Patient.get_all()
        

        page = request.args.get('page', 1, type=int)
        per_page = 5
        total_items = len(patient_profiles)
        total_pages = math.ceil(total_items / per_page)

        start = (page - 1)*per_page
        end = start + per_page
        paginated_patient_profiles = patient_profiles[start:end]
        
        return render_template('components/admin/admin-view-patient.html', patient_profiles=paginated_patient_profiles, page=page, total_pages=total_pages)
    
    return redirect(url_for('index'))


@app.route('/admin-view-patient-profile/<patient_id>', methods=['GET'])
def view_patient_profile(patient_id):
    patient_profile = Patient.get_by_id(ObjectId(patient_id))

    if patient_profile:
        patient_profile['_id'] = str(patient_profile['_id'])
        return jsonify(patient_profile)
    return jsonify({'error': 'Patient profile not found'})



@app.route('/admin-patient-profile-status-update/<patient_id>', methods=['GET','POST'])
def admin_patient_profile_status_update(patient_id):
    if 'admin_id' in session:
        patient = Patient.get_by_id(ObjectId(patient_id))

        if patient:
            if request.method == 'POST':

                status = request.form['status']

                update_data = {
                    'status': status
                }
                        

                # Update doctor details in the database
                Patient.update(ObjectId(patient_id), update_data)

                return jsonify({'success': "Profile Updated"})
        else:
            return redirect(url_for('index'))


@app.route('/admin-delete-patient-profile', methods = ['GET', 'POST'])
def admin_delete_patient_profile():
    data = request.get_json()
    patient_id = data.get('patient_id')

    if patient_id:
        Patient.delete_patient_profile(ObjectId(patient_id))
        return jsonify({'success': 'Profile deleted'})
    return jsonify({'error': 'No profile ID provided'})


@app.route('/admin-appointment-management')
def admin_appointment_management():
    if 'admin_id' in session:
        return render_template('admin/admin-appointment-management.html')
    return redirect(url_for('index'))





@app.route('/login', methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        patient = Patient.authenticate(email, password)

        if patient:
            session['patient_id'] = str(patient['_id'])  # Store user ID in session
            session['patient_email'] = patient['email']
            return redirect(url_for('patient_home'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('patient-login.html')



@app.route('/register', methods = ['GET','POST'])
def register():
    if request.method == 'POST':
        fullName = request.form['fullname']
        email = request.form['email']
        password = request.form['confirm-password']
        hashed_password = Patient.hash_password(password)

        patient = Patient(fullName, email, hashed_password)
        patient.save()
        return redirect(url_for('login'))
    return render_template('patient-register.html')





    

if __name__ == '__main__':
    app.run(debug=True)