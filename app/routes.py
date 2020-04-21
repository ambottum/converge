import csv, json, sys
import os
#from ocr_core import ocr_core
from app import app,login, db
from flask import render_template, request, send_from_directory
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm
from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename

#reading in env variable for UPLOAD_FOLDER from __init__.py
UPLOAD_FOLDER=app.config['UPLOAD_FOLDER']
# allow files of a specific type
ALLOWED_EXTENSIONS = set(['csv','xls','xlsx'])

# function to check the file extension
def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {'username': 'Miguel'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Converge Home', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('upload_file'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
                        #next_page = request.args.get('next')
                        #if not next_page or url_parse(next_page).netloc != '':
                        #    next_page = url_for('upload_file')
        return redirect(url_for('upload_file'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    imports = [
        {'analyst': user, 'file_name': 'File #1'},
        {'analyst': user, 'file_name': 'File #2'}
    ]
    return render_template('user.html', user=user, imports=imports)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_login = datetime.utcnow()
        db.session.commit()

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
    # check if there is a file in the request
        if 'file1' not in request.files and 'file2' not in request.files:
            return render_template('upload.html', msg='No file selected')
        file1 = request.files['file1']
        file2 = request.files['file2']
        # if no file is selected
        if file1.filename == '' and file2.filename == '':
            return render_template('upload.html', msg='No file selected')
        if file1 and allowed_file(file1.filename) and file2 and allowed_file(file2.filename):
            filename1 = secure_filename(file1.filename)
            filename2 = secure_filename(file2.filename)
            file1.save(os.path.join(app.config['UPLOAD_FOLDER'], filename1))
            file2.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2))
            #return redirect(url_for('uploaded_file',filename=filename))
            img_src1=UPLOAD_FOLDER + "/" + file1.filename
            img_src2=UPLOAD_FOLDER + "/" + file2.filename
            with open(img_src1) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        headers1 = row
                        line_count += 1
                    else:
                        line_count += 1
            with open(img_src2) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                line_count = 0
                for row in csv_reader:
                    if line_count == 0:
                        headers2 = row
                        line_count += 1
                    else:
                        line_count += 1              
            return render_template('upload.html', msg='File Succesfully Uploaded', 
                                    filename1=file1.filename, filename2=file2.filename, 
                                    headers1=headers1, headers2=headers2) 
            print('filename1 is: ',filename1)
            print('filename2 is: ',filename2)

            #file.save(secure_filename(file.filename))
            # if True:


    elif request.method == 'GET':
        return render_template('upload.html')

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'],
#                                filename)
