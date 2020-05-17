import csv, json, sys
import os
import pandas as pd
from app import app,login, db
from flask import render_template, request, send_from_directory
from werkzeug.urls import url_parse
from app.forms import LoginForm, RegistrationForm, HiddenPaths, HiddenFields
from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename
from collections import Counter

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
    posts = []
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
        if file1.filename == '' or file2.filename == '':
            flash('Please be sure to select two files')
            return render_template('upload.html', msg='No file selected')
        if file1 and allowed_file(file1.filename) and file2 and allowed_file(file2.filename):
            filename1 = secure_filename(file1.filename)
            filename2 = secure_filename(file2.filename)
            file1.save(os.path.join(app.config['UPLOAD_FOLDER'], filename1))
            file2.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2))
            img_src1=UPLOAD_FOLDER + "/" + file1.filename
            img_src2=UPLOAD_FOLDER + "/" + file2.filename

            form=HiddenPaths(path1=img_src1, path2=img_src2)

            with open(img_src1) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                line_count = 0
                #every row is a list
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

            #replace spaces with underscores so that header names can be passed to html
            headers1_ = []  
            headers2_ = []          
            for i in range(len(headers1)):
                headers1[i] = headers1[i].replace(" ","_")
                headers1_.append(headers1[i].replace("_"," "))
            for i in range(len(headers2)):
                headers2[i] = headers2[i].replace(" ","_")
                headers2_.append(headers2[i].replace("_"," "))
            print(headers1_)
            return render_template('upload.html', msg='File Succesfully Uploaded', 
                                    filename1=file1.filename, filename2=file2.filename, 
                                    headers1=headers1, headers2=headers2, headers1_=headers1_,
                                    headers2_=headers2_,form=form)

    elif request.method == 'GET':
        return render_template('upload.html')



@app.route('/merged_file', methods=['GET', 'POST'])
def get_headers():
    if request.method == 'POST':
        form = HiddenPaths(request.values)
        path1 = form.data['path1']
        path2 = form.data['path2']
        filename1 = form.data['path1'].split("/")[-1]
        filename2 = form.data['path2'].split("/")[-1]
        no_zero = request.form.getlist('no_zero')

        """
        merge_headers is a list of all values that are checked
        first pass will have a list of merge_headers directly
        from upload.html, so first pass will enter if statement
        """

        if request.form.getlist('file1'):
            merge_headers1 = request.form.getlist('file1')
            merge_headers2 = request.form.getlist('file2')

            if 'fkey1' not in request.form.keys() or 'fkey2' not in request.form.keys():
                flash('Please be sure to select a primary key for each file')
                return render_template('upload.html')

            foreign_key1 = request.form['fkey1']
            foreign_key2 = request.form['fkey2']

            """
            turn above items into lists so that they can be 
            packed into HiddenForm and unpacked in else statement
            """

            mh_string1 = ','.join(merge_headers1)
            mh_string2 = ','.join(merge_headers2)

            form = HiddenFields(path1=path1, path2=path2,
                hmerge_headers1=mh_string1, hmerge_headers2=mh_string2,
                hforeign_key1=foreign_key1, hforeign_key2=foreign_key2)
          
            if no_zero and no_zero[0] == 'on':
                return render_template('ignore_fields.html',
                    merge_headers1=merge_headers1, merge_headers2=merge_headers2,
                    filename1=filename1, filename2=filename2, form=form)

            #second pass will NOT have a list of merge_headers because it is coming from ignore_fields. so we need to grab the list of merge_headers from the hiddenforms
        else:
            form_fields = HiddenFields(request.values)
            form_paths = HiddenPaths(request.values)

            path1 = form_paths.data['path1']
            path2 = form_paths.data['path2']

            filename1=form_paths.data['path1'].split("/")[-1]

            filename2=form_paths.data['path2'].split("/")[-1]

            merge_headers1 = form_fields.data['hmerge_headers1'].split(",")
            merge_headers2 = form_fields.data['hmerge_headers2'].split(",")
            foreign_key1 = form_fields.data['hforeign_key1']
            foreign_key2 = form_fields.data['hforeign_key2']

            if not merge_headers1[0] or not merge_headers2[0]:
                flash('Please be sure to select data to merge')
                return render_template('upload.html')
        
            no_zero = [] #make no_zero an empty list so that it doesn't enter if statement below

        #checking to see if ignore_field1 or ignore_field2 (or both) were checked. if not, sets equal to null
        df1 = pd.read_csv(path1)
        df2 = pd.read_csv(path2)

        ignore_msg = ""
        if 'ignore_field1' in request.form.keys():
            if 'ignore_field1' not in df1.columns:
                ignore_field1 = request.form['ignore_field1'].replace("_"," ")
            ignore_value1 = request.form['ignore_value1']
        else:
            ignore_field1 = None
               
        if 'ignore_field2' in request.form.keys():    
            if 'ignore_field2' not in df2.columns:
                ignore_field2 = request.form['ignore_field2'].replace("_"," ")
            ignore_value2 = request.form['ignore_value2']
        else:
            ignore_field2 = None

        if ignore_field1:
            ignore1_count = len(df1[df1[ignore_field1] == ignore_value1])
            ignore_msg = ignore_msg + "Excluded "+ignore_value1+" values from "+filename1+" "+str(ignore1_count)+" times \n"
            df1 = df1.loc[df1[ignore_field1] != ignore_value1]
        else:
            ignore1_count = None
            ignore_value1 = None

        if ignore_field2:
            ignore2_count = len(df2[df2[ignore_field2] == ignore_value2])
            ignore_msg = ignore_msg + "Excluded "+ignore_value2+" values from "+filename2+" "+str(ignore2_count)+" times \n" 
            df2 = df2.loc[df2[ignore_field2] != ignore_value2]
        else:
            ignore2_count = None
            ignore_value2 = None
   
        merge_headers1.append(foreign_key1)
        merge_headers2.append(foreign_key2)

        """
        check to see if column names' syntax match what is in natural 
        state of files. If not, add spaces where there are underscores
        """

        for i in range(len(merge_headers1)):
            if merge_headers1[i] not in df1.columns:
                merge_headers1[i] = merge_headers1[i].replace("_"," ")
        for i in range(len(merge_headers2)):
            if merge_headers2[i] not in df2.columns:
                merge_headers2[i] = merge_headers2[i].replace("_"," ")
        if foreign_key1 not in df1.columns:             
            foreign_key1 = foreign_key1.replace("_"," ")
        if foreign_key2 not in df2.columns:
            foreign_key2 = foreign_key2.replace("_"," ")

        df1 = df1[merge_headers1]
        df2 = df2[merge_headers2]

        print("foreign_key1", foreign_key1)
        print("foreign_key2", foreign_key2)
        print(df1.columns)
        print(df2.columns)

        #get percentage of merge matches
        matches = set(df1[foreign_key1]).intersection(set(df2[foreign_key2]))
        percent = len(matches) / len(df1) * 100.00
        print('PERCENT ',percent)

        if percent <= 0:
            flash('Primary key match was less than 1%, is there a better join field?')
            return render_template('upload.html')
        else:
            msg = str(round(percent,2))+"% of rows in File 1 matched File 2"


            save_file=filename1[:-4]+"-"+filename2[:-4]+".csv"
            file_src=UPLOAD_FOLDER + "/" + save_file      
            merged_file = pd.merge(df1, df2, left_on = foreign_key1, right_on = foreign_key2, how='left')           
            merged_file.to_csv(file_src)

        return render_template('merged_file.html', msg=msg,
            ignore_msg=ignore_msg, ignore_value1=ignore_value1,
            ignore_value2=ignore_value2, ignore1_count=ignore1_count,
            ignore2_count=ignore2_count, merge_headers1=merge_headers1,
            merge_headers2=merge_headers2, foreign_key1=foreign_key1,
            foreign_key2=foreign_key2, form=form, no_zero=no_zero,
            UPLOAD_FOLDER=UPLOAD_FOLDER, save_file=save_file,
            filename1=filename1, filename2=filename2) 
    elif request.method == 'GET':
        return render_template('upload.html')        

