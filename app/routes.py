import csv, json, sys
import os
import pandas as pd 
#from ocr_core import ocr_core
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
            #replace spaces with underscores             
            for i in range(len(headers1)):
                headers1[i] = headers1[i].replace(" ","_")
            for i in range(len(headers2)):
                headers2[i] = headers2[i].replace(" ","_")
            return render_template('upload.html', msg='File Succesfully Uploaded', 
                                    filename1=file1.filename, filename2=file2.filename, 
                                    headers1=headers1, headers2=headers2, form=form) 

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

        #merge_headers is a list of all values that are checked 
        #first pass will have a list of merge_headers directly from upload.html, so first pass will enter if statement
        if request.form.getlist('file1'):
            merge_headers1 = request.form.getlist('file1')
            merge_headers2 = request.form.getlist('file2')

            foreign_key1 = request.form['fkey1']
            foreign_key2 = request.form['fkey2']

            #turn above items into lists so that they can be packed into HIddenForm and unpacked in else statement
            mh_string1 = ','.join(merge_headers1)
            mh_string2 = ','.join(merge_headers2)

            form = HiddenFields(path1=path1, path2=path2, hmerge_headers1=mh_string1, hmerge_headers2=mh_string2, hforeign_key1=foreign_key1, hforeign_key2=foreign_key2)
          
            
            print("FIRST PASS merge_headers1 ",merge_headers1)
            #return render_template('ignore_fields.html', merge_headers1=merge_headers1, merge_headers2=merge_headers2, filename1=filename1, filename2=filename2, form=form)

            print("JUST BEFORE NOZERO IF", form)
            if no_zero and no_zero[0] == 'on':
                print("NO_ZERO ",no_zero)
                return render_template('ignore_fields.html', merge_headers1=merge_headers1, merge_headers2=merge_headers2, filename1=filename1, filename2=filename2, form=form)

            #return render_template('merged_file.html')    

            #second pass will NOT have a list of merge_headers because it is coming from ignore_fields. so we need to grab the list of merge_headers from the hiddenforms
        else:
            print("SECOND PASS ", request.values.__dict__)
            form_fields = HiddenFields(request.values)
            form_paths = HiddenPaths(request.values)

            path1 = form_paths.data['path1']
            path2 = form_paths.data['path2']

            filename1=form_paths.data['path1'].split("/")[-1]
            print("FILENAME1 IS ",filename1)
            filename2=form_paths.data['path2'].split("/")[-1]

            merge_headers1 = form_fields.data['hmerge_headers1'].split(",")
            merge_headers2 = form_fields.data['hmerge_headers2'].split(",")
            foreign_key1 = form_fields.data['hforeign_key1']
            foreign_key2 = form_fields.data['hforeign_key2']
            
            no_zero = [] #make no_zero an empty list so that it doesn't enter if statement below
        
        ## TO DO remove hardcoding of Transacation Amt & $0
        # print("JUST BEFORE NOZERO IF", form)
        # if no_zero and no_zero[0] == 'on':
        #     print("NO_ZERO ",no_zero)
        #     return render_template('ignore_fields.html', merge_headers1=merge_headers1, merge_headers2=merge_headers2, filename1=filename1, filename2=filename2, form=form)
        #checking to see if ignore_field1 or ignore_field2 (or both) were checked. if not, sets equal to null
        
        if 'ignore_field1' in request.form.keys():    
            ignore_field1 = request.form['ignore_field1'].replace("_"," ")
        else:
            ignore_field1 = None
        if 'ignore_field2' in request.form.keys():    
            ignore_field2 = request.form['ignore_field2'].replace("_"," ")
        else: 
            ignore_field2 = None    

        #this will be the pandas code here
        #open spreadsheets to begin merge process
        df1 = pd.read_csv(path1)
        df2 = pd.read_csv(path2)
        if ignore_field1:
            df1 = df1.loc[df1[ignore_field1] != '$0.00']
        if ignore_field2:
            print("DF2 HEADERS ",df2.head())    
            df2 = df2.loc[df2[ignore_field2] != '$0.00']

        for i in range(len(merge_headers1)): 
            merge_headers1[i] = merge_headers1[i].replace("_"," ")
        for i in range(len(merge_headers2)):
            merge_headers2[i] = merge_headers2[i].replace("_"," ")        
        foreign_key1 = foreign_key1.replace("_"," ")
        foreign_key2 = foreign_key2.replace("_"," ")

        
        #THIS IS NEW CODE ADDED ON SUNDAY 4/26
        df2.rename(columns = {foreign_key2:foreign_key1}, inplace = True)
        merge_headers1.append(foreign_key1)
        merge_headers2.append(foreign_key1)
        df1 = df1[merge_headers1]
        df2 = df2[merge_headers2]
        

        #no_zero = request.form
        #check if user wants to exclude zeros
        
        save_file=filename1[:-4]+"-"+filename2[:-4]+".csv"
        file_src=UPLOAD_FOLDER + "/" + save_file      
        merged_file = pd.merge(df1, df2, on = foreign_key1, how='left')
        merged_file.to_csv(file_src)


        #Create intermediate report of just air travel info from Transaction Detail Rpt
        # int_air = data.loc[data['Merchant Category Code Group Description'] == 'AIRLINE']
        #search_by = search_by.loc[search_by['Transaction Amount'] != '$0.00']

        # USB = pd.merge()
        # USB = pd.merge((int_air[cols_needed]),search_by, on=['Merchant Name'])










        return render_template('merged_file.html', msg='Files Succesfully Merged', merge_headers1=merge_headers1, merge_headers2=merge_headers2, foreign_key1=foreign_key1, foreign_key2=foreign_key2, form=form, no_zero=no_zero, UPLOAD_FOLDER=UPLOAD_FOLDER, save_file=save_file, filename1=filename1, filename2=filename2) 
    elif request.method == 'GET':
        return render_template('upload.html')        



# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'],
#                                filename)
