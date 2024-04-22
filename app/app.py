from flask import Flask, request, redirect, render_template, flash, session, jsonify, url_for
from DBcm import UseDatabase
from werkzeug.utils import secure_filename
import os
import base64
import cv2
import face_recognition
import numpy as np
from PIL import Image
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

app.config["dbconfig"]={'host': 'mariadb',
                        'user': 'vsearch',
                        'password': 'vsearchpasswd',
                        'database': 'facereader',}


#撮影写真の相対パス
app.config['KNOWN_FACES_FOLDER'] = 'static/img_faces'

######################################################################################
#以下ログイン(登録済み)


#flagがtrueならwelcome.htmlに画面遷移, falseは/login(GET)を呼ぶ
@app.route('/')
def index():
    if "flag" in session and session["flag"]:
        return render_template('welcome.html', username=session["username"])
    return redirect('/login')

#flagがtrueなら/welcome, false はlogin.html(学籍番号入力画面)に画面遷移
@app.route('/login', methods=['GET'])
def login():
    if 'flag' in session and session['flag']:
        return redirect('/welcome')
    return render_template('login.html')

#login.html(学籍番号入力画面)で入力された情報を獲得.
@app.route('/login', methods=['POST'])
def login_post():
    studentnumber = request.form["studentnumber"]
    #入力情報をDBと参照し, DBと一致がなければsession["flag"]にfalseを返し, 一致すればsession["flag"]にTrueを返す.
    with UseDatabase(app.config["dbconfig"]) as cursor:
        SQL = "SELECT * FROM Userlist WHERE studentid = {} ;".format(studentnumber)
        cursor.execute(SQL)
        data = cursor.fetchall()
        #以下はDBと一致しない時の処理
        if data == []:
            flash('学籍番号が間違っているか登録されていません','ng')
            session['flag'] = False
        
        #以下はDBと一致した時の処理
        else:
            session["flag"] = True
            session['studentnumber'] = data[0][0]
            session["username"] = data[0][1]
            SQL = "INSERT INTO Attendance values(null, {}, '{}', now());".format(session['studentnumber'], session["username"] )
            cursor.execute(SQL)

        #sessin["flag"]がTrueの時, welcome.htmlに画面遷移. 違った場合は/login(GET)を呼ぶ. 
        if session["flag"]:
            return render_template('welcome.html', studentnumber=session["studentnumber"], username=session["username"])
        else:
            return redirect('/login')

#flagがtrueならwelcome.htmlに画面遷移, falseは/login(GET)を呼ぶ
@app.route('/welcome')
def welcome():
    if "flag" in session and session["flag"]:
        return render_template('welcome.html', username=session["username"])
    return redirect('/login')

######################################################################################
#以下新規登録(流れはログインと類似)
#login.htmlから呼び出されている


#flagがtrueならwelcome.htmlに画面遷移, falseは/new_account_create(GET)を呼ぶ
@app.route('/new_account')
def new_account():
    if "flag" in session and session["flag"]:
        return render_template('new_account_welcome.html', new_studentnumber=session["new_studentnumber"], new_username=session["new_username"])
    return redirect('/new_account_create')

#flagがtrueなら/welcome, false はnew_account.html(新規登録)に画面遷移
@app.route('/new_account_create', methods=['GET'])
def new_account_create():
    if 'flag' in session and session['flag']:
        return redirect('/new_account_welcome')
    return render_template('new_account.html')

#new_account.html(新規登録)で入力された情報を獲得.
#もし学生証番号が既に登録されてた場合, Flagにfalseを返す.　登録されていない時,入力された学生証番号と氏名をsessionにいれ, 入力確認画面に遷移
@app.route('/new_account_create', methods=['POST'])
def new_account_create_post():
    new_studentnumber =request.form["new_studentnumber"]
    new_username = request.form["new_username"]
    with UseDatabase(app.config["dbconfig"]) as cursor:
        SQL = "SELECT * FROM Userlist WHERE studentid = {} ;".format(new_studentnumber)
        cursor.execute(SQL)
        data = cursor.fetchall()
        #以下はDBに登録がなかった場合の処理
        if data == []:
            session["new_studentnumber"] = new_studentnumber
            session["new_username"] = new_username
            session["flag"] = True

        #以下はDBに登録が既にある場合の処理
        else: 
            flash('学籍番号はすでに登録されています','ng')
            session['flag'] = False

    if "flag" in session and session["flag"]:
        return render_template('new_account_face_reader.html', new_studentnumber=session["new_studentnumber"], new_username=session["new_username"])
    return redirect('/new_account_create')

#入力確認画面でOKを押した時の動作. DBの新規登録と, 出席登録をしている.
@app.route('/new_account_complete')
def new_account_complete():
    if "flag" in session and session["flag"]:
        with UseDatabase(app.config["dbconfig"]) as cursor:
            SQL = "INSERT INTO Userlist values({}, '{}');".format(session['new_studentnumber'], session["new_username"] )
            cursor.execute(SQL)

            SQL = "INSERT INTO Attendance values(null, {}, '{}', now());".format(session['new_studentnumber'], session["new_username"] )
            cursor.execute(SQL)
        return render_template('new_account_welcome.html', new_studentnumber=session["new_studentnumber"], new_username=session["new_username"])
    return redirect('/new_account_create')

@app.route('/new_account_re_enter')
def new_account_re_enter():
    # Generate filename based on the student number and username in session
    filename = f"{session['new_studentnumber']}_{session['new_username']}.jpg"

    # Define the path of the file
    path = os.path.join(app.config['KNOWN_FACES_FOLDER'], filename)

    # Check if file exists and remove it
    if os.path.exists(path):
        os.remove(path)

    # Reset session data
    session.pop('new_studentnumber', None)
    session.pop('username', None)
    session.pop("flag", None)
    session["new_studentnumber"] = None
    session["new_username"] = None
    session["flag"] = False

    return redirect("/new_account_create")
#flagがtrueならnew_account_welcome.htmlに画面遷移, falseは/new_account_create(GET)を呼ぶ
@app.route('/new_account_welcome')
def new_account_welcome():
    if "flag" in session and session["flag"]:
        return render_template('new_account_welcome.html', new_studentnumber=session["new_studentnumber"], new_username=session["new_username"])
    return redirect('/new_account_create')


##########################################################################################################################
#これは顔認証

@app.route('/register', methods=['POST'])
def register():
    # Get the image data from the request body
    image_data = request.json['image']

    # Remove header from image data
    image_data = image_data.split(',', 1)[1]

    # Convert base64 image to bytes
    image_bytes = base64.b64decode(image_data)

    # Generate a filename based on the student number and username in session
    filename = f"{session['new_studentnumber']}_{session['new_username']}.jpg"

    # Save the image in the known_faces folder
    with open(os.path.join(app.config['KNOWN_FACES_FOLDER'], filename), 'wb') as f:
        f.write(image_bytes)

    # Store the image filename in session
    session['image_filename'] = filename

    # return the message instead of redirecting
    return jsonify({'message': 'Registered successfully!', 'filename': filename})



@app.route('/new_account_check', methods=['GET'])
def new_account_check_get():
    image_filename = url_for('static', filename='img_faces/' + session.get('image_filename'))
    return render_template('new_account_check.html', 
                           new_studentnumber=session.get('new_studentnumber'), 
                           new_username=session.get('new_username'),
                           image_filename= image_filename)




@app.route('/verify', methods=['POST'])
def verify():

    # Load all images from static/img_faces directory
    known_face_encodings = []
    known_face_names = []

    for filename in os.listdir('static/img_faces'):
        if filename.endswith(".jpg"):
            image = face_recognition.load_image_file(os.path.join('static/img_faces', filename))
            face_encodings = face_recognition.face_encodings(image)
            if len(face_encodings) > 0:  # If a face is found in the image
                known_face_encodings.append(face_encodings[0])
                known_face_names.append(filename.split('.')[0])  # Assuming the filename without extension is the name
            

    # Get the image data from the request body
    image_data = request.get_json()['image']

    # Remove header from image data
    image_data = image_data.split(',', 1)[1]

    # Convert base64 image to numpy array
    image_bytes = base64.b64decode(image_data)
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Resize the frame for faster processing
    small_frame = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    # If no faces are detected, continue processing
    if len(face_encodings) == 0:
        return jsonify({'message': 'No faces detected. Continuing video.', 'name': 'Unknown'})

    # Compare each detected face to known faces
    names = []
    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s) この閾値を変更すると精度が変わる. 
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding,  tolerance=0.5)
        name = "Unknown"

        # Use the known face with the smallest distance to the new face
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]

        names.append(name)

    return jsonify({'message': 'Processed successfully!', 'name': names[0]})

@app.route('/ok')
def ok():
    name = request.args.get('name')
    studentnumber = name.split('_')[0]
    with UseDatabase(app.config["dbconfig"]) as cursor:
        SQL = "SELECT * FROM Userlist WHERE studentid = {} ;".format(studentnumber)
        cursor.execute(SQL)
        data = cursor.fetchall()
    
        # ユーザー情報をセッションに保存
        session["flag"] = True
        session['studentnumber'] = data[0][0]
        session["username"] = data[0][1]
    
        # 出席情報をDBに保存
        SQL = "INSERT INTO Attendance values(null, {}, '{}', now());".format(session['studentnumber'], session["username"])
        cursor.execute(SQL)

        if session["flag"]:
            return render_template('welcome.html', studentnumber=session["studentnumber"], username=session["username"])
        else:
            return redirect('/login')
        
################################################################################################################################################
@app.route('/attendance')
def attendance():
    data = []
    with UseDatabase(app.config["dbconfig"]) as cursor:
        attendancelist = "SELECT * FROM Attendance"
        cursor.execute(attendancelist)
        attendancelist = cursor.fetchall()
        for item in attendancelist:
            number = item[0]
            studentnumber = item[1]
            name = item[2]
            date = item[3]
            photo = None  # set default as None

            for filename in os.listdir('static/img_faces/'):
                split_filename = filename.split('_')  # split the filename
                
                if split_filename[0] == str(studentnumber):  # check if it matches the student number
                    photo = filename  # if it does, save the filename
                    break

            data.append((studentnumber, name, date, number, photo))
        return render_template('attendancelist.html', data = data)

@app.route('/attendance_count')
def attendance():
    data = []
    with UseDatabase(app.config["dbconfig"]) as cursor:
        attendancelist = "SELECT studentid, name, COUNT(*) AS count FROM Attendance GROUP BY studentid, name"
        cursor.execute(attendancelist)
        attendancelist = cursor.fetchall()
        for item in attendancelist:
            studentnumber = item[0]
            name = item[1]
            count = item[2]
            photo = None  # set default as None

            for filename in os.listdir('static/img_faces/'):
                split_filename = filename.split('_')  # split the filename
                
                if split_filename[0] == str(studentnumber):  # check if it matches the student number
                    photo = filename  # if it does, save the filename
                    break

            data.append((studentnumber, name, count, photo))
        return render_template('attendancelist_count.html', data = data)
    
@app.route('/attendance_delete_all')
def delete():
    with UseDatabase(app.config["dbconfig"]) as cursor:
        SQL = "truncate table Attendance;"
        cursor.execute(SQL)
    return render_template('attendancelist.html')

@app.route('/attendance_delete_one')
def attendance_delete_one():
    with UseDatabase(app.config["dbconfig"]) as cursor:
        deleteid = request.args.get('number')
        SQL = "DELETE FROM Attendance WHERE number = '{}';".format(deleteid)
        cursor.execute(SQL)
    
    data = []
    with UseDatabase(app.config["dbconfig"]) as cursor:
        attendancelist = "SELECT * FROM Attendance"
        cursor.execute(attendancelist)
        attendancelist = cursor.fetchall()
        for item in attendancelist:
            number = item[0]
            studentnumber = item[1]
            name = item[2]
            date = item[3]
            photo = None  # set default as None

            for filename in os.listdir('static/img_faces/'):
                split_filename = filename.split('_')  # split the filename
                
                if split_filename[0] == str(studentnumber):  # check if it matches the student number
                    photo = filename  # if it does, save the filename
                    break

            data.append((studentnumber, name, date, number, photo))
    return render_template('attendancelist.html', data = data)

@app.route('/delete_Userlist')
def Delete_Userlist():
    try:
        with UseDatabase(app.config["dbconfig"]) as cursor:
            deleteid = request.args.get('studentID')
            SQL = "DELETE FROM Userlist WHERE studentid = '{}';".format(deleteid)
            cursor.execute(SQL)
    except Exception as e:
        flash("出席一覧に同じ学生番号がいます. そちらから先に削除してください")
        return redirect('/Userlist')
    
    data = []
    with UseDatabase(app.config["dbconfig"]) as cursor:
        attendancelist = "SELECT * FROM Userlist"
        cursor.execute(attendancelist)
        attendancelist = cursor.fetchall()
        for item in attendancelist:
            studentnumber = item[0]
            name = item[1]
            data.append((studentnumber, name))
    return render_template('Userlist.html',data = data )
    

@app.route('/Userlist')
def list():
    data = []
    with UseDatabase(app.config["dbconfig"]) as cursor:
        attendancelist = "SELECT * FROM Userlist"
        cursor.execute(attendancelist)
        attendancelist = cursor.fetchall()
        for item in attendancelist:
            studentnumber = item[0]
            name = item[1]
            data.append((studentnumber, name))
        return render_template('Userlist.html', data = data)

####################################################################################################################

#ログアウト, 全ての情報を消しておく
@app.route('/logout',methods=['POST'])
def logout():
    session.pop('new_studentnumber', None)
    session.pop('username', None)
    session.pop("flag", None)
    session["new_studentnumber"] = None
    session["new_username"] = None
    session["flag"] = False
    return redirect("/login")


#以下はheaderのhomeを押した時に対応
@app.route('/logout')
def logout_header():
    session.pop('new_studentnumber', None)
    session.pop('username', None)
    session.pop("flag", None)
    session["new_studentnumber"] = None
    session["new_username"] = None
    session["flag"] = False
    return redirect("/login")


if __name__ == '__main__':
  app.run(debug=True)