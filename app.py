from flask import Flask, render_template, url_for, redirect, request, session, flash, make_response
from models import Patient, Doctor, Admin

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


@app.route('/doctor-home')
def doctor_home():
    if 'doctor_id' in session:
        return render_template('doctor/doctor-home.html')
    return redirect(url_for('index'))


@app.route('/patient-home')
def patient_home():
    if 'patient_id' in session:
        patient_id = session['patient_id']
        return render_template('patient/patient-home.html', patient_id = patient_id)
    return redirect(url_for('index'))

@app.route('/admin-home')
def admin_home():
    if 'admin_id' in session:
        return render_template('admin/admin-home.html')
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


@app.route('/login-doctor', methods = ['GET','POST'])
def doctor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        doctor = Doctor.authenticate(email, password)

        if doctor:
            session['doctor_id'] = str(doctor['_id'])  # Store user ID in session
            session['doctor_email'] = doctor['email']
            return redirect(url_for('doctor_home'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('doctor-login.html')


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
        doctor.save()
        return redirect(url_for('doctor_login'))

    return render_template('doctor-register.html')



if __name__ == '__main__':
    app.run(debug=True)