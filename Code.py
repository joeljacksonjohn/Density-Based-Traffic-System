Flask Backend 

Application Website Interface

import smtplib
from email.mime.text import MIMEText

from flask import *
import pymysql
flow = Flask(__name__)
con = pymysql.connect(host='localhost',user='root',password='root',db='smartsignalhub',charset='utf8')
cmd = con.cursor()

@flow.route("/userregister", methods=['GET', 'POST'])
def userregister():
    data = request.json
    print(data)
    name = data.get("name")
    phone = data.get("phone")
    email = data.get("email")
    rc = data.get("rcNumber")
    adhr = data.get("adharNumber")
    password = data.get("password")
    usertype = data.get("usertype")
    emer_id = data.get("id")

    print(name, phone, email, rc, adhr, password, usertype, emer_id)

    # Check for existing data
    cmd.execute("""
        SELECT rc_number, emergency_id 
        FROM userreg 
        WHERE rc_number=%s OR  emergency_id=%s
    """, (rc,emer_id))
    res = cmd.fetchone()
    print("res:", res)

    if res is None:
        # Insert into login table
        cmd.execute("INSERT INTO login (email, password, type, otp) VALUES (%s, %s, 'pending', NULL)",
                    (email, password))

        loginid = cmd.lastrowid

        # Insert into userreg table
        cmd.execute("""
            INSERT INTO userreg (email, name, phone, rc_number, aadhar_number, login_id, usertype, emergency_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (email, name, phone, rc, adhr, loginid, usertype, emer_id if emer_id else None))

        con.commit()
        return jsonify({'task': "Successfully inserted"})
    else:
        # Identify which data already exists
        existing_data = []
        if res[0] == rc:
            existing_data.append("RC Number already exists.")

        if res[1] == emer_id:
            existing_data.append("Emergency ID already exists.")

        return jsonify({'task': "Failed", 'existing_data': existing_data})


@flow.route("/logincheck",methods=['get','post'])
def logincheck():
    print(request.args)
    email = request.args.get("username")
    passwrd = request.args.get("password")
    cmd.execute("select * from login where email='"+str(email)+"' and password='"+str(passwrd)+"'")
    result = cmd.fetchone()
    print(result)
    if result is None:
        return jsonify({'task': "invalid"})
    elif result[3] == 'user':
        return jsonify({'task': "success",'loginid': result[0],'type':result[3]})
    elif result[3] == 'admin':
        return jsonify({'task':"success",'loginid':result[0],'type':result[3]})
    elif result[3] == 'emergency':
        return jsonify({'task': "success", 'loginid': result[0], 'type': result[3]})
    else:
        return jsonify({'task': "failed"})

@flow.route("/getprofile",methods=['get','post'])
def getprofile():
    id=request.args.get("lid")
    print(id)
    cmd.execute("SELECT * FROM `userreg` WHERE `login_id`='"+id+"'")
    s=cmd.fetchone()
    print(s)
    header=[x[0] for x in cmd.description]
    json_data=[]
    if s:
        json_data.append(dict(zip(header, s)))
        print(json_data)
    return jsonify(json_data)

@flow.route("/updateprofiledetails",methods=['get','post'])
def updateprofiledetails():
    data = request.json
    print(data)
    name = data.get("name")
    phone = data.get("phone")
    lid = data.get("lid")
    cmd.execute("update userreg details set name='"+name+"',phone='"+phone+"' where login_id='"+lid+"'")
    con.commit()
    return jsonify({'task':"success"})

@flow.route("/deleteuser",methods=['get','post'])
def deleteuser():
    logid = request.args.get("login_id")
    cmd.execute("delete from user_registration where login_id='"+str(logid)+"'")
    con.commit()
    cmd.execute("DELETE FROM `login` WHERE `login_id`='"+str(logid)+"'")
    con.commit()
    return jsonify({'task':"success"})


@flow.route("/congestion_alerts",methods=['get','post'])
def congestion_alerts():
    cmd.execute("SELECT * FROM `alerts` where alert_type='congestion'")
    # return jsonify({'task': "success"})
    s = cmd.fetchall()
    header = [x[0] for x in cmd.description]
    json_data = []
    for result in s:
        json_data.append(dict(zip(header, result)))
        print(json_data)
    return jsonify(json_data)

@flow.route("/changepassword",methods=['get','post'])
def changepassword():
    oldpassword = request.args.get("oldpassword")
    newpassword = request.args.get("newpassword")
    cmd.execute("select * from login where password='"+oldpassword+"'")
    result = cmd.fetchone()
    if result is None:
        return jsonify({'task': "Invalid"})
    else:
        cmd.execute("UPDATE login SET PASSWORD='"+newpassword+"' WHERE PASSWORD='"+oldpassword+"'")
        con.commit()
        return jsonify({'task': "Updated Succeccfully"})
    return jsonify({'task': "success"})



@flow.route("/traffic_control",methods=['get','post'])
def traffic_control():
    print(request.form)
    Time = request.form.get("time")
    Date = request.form.get("date")
    Location = request.form.get("location")
    route = request.form.get("route")
    loginid = request.form.get("loginid")
    cmd.execute("INSERT INTO traffic_control VALUES(NULL,'"+Time+"','"+Date+"','"+Location+"','"+route+"','"+str(loginid)+"')")
    con.commit()
    return jsonify({'task': "success"})


@flow.route("/livestats", methods=['get','post'])
def livestats():
    cmd.execute("SELECT * FROM congestion")
    s = cmd.fetchall()
    print(s)
    header = [x[0] for x in cmd.description]
    json_data = []
    for result in s:
        # Convert timedelta object to string representation
        result = list(result)
        result[1] = str(result[1])
        json_data.append(dict(zip(header, result)))
        print(json_data)
    return jsonify(json_data)
@flow.route('/sendfeedback',methods=['post','get'])
def sendfeedback():
    id=request.args.get('lid')
    feedback=request.args.get('feedback')
    cmd.execute("insert into feedback values(null,'"+feedback+"','"+str(id)+"')")
    con.commit()
    return jsonify({'task': "success"})


from datetime import datetime


@flow.route('/sendemergencyalert', methods=['POST', 'GET'])
def sendemergencyalert():
    lid = request.args.get('lid')
    data = request.get_json()
    print(data, '***********')

    location = data.get('location')
    alert = data.get('alert')

    # Get current date and time
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")  # Format: YYYY-MM-DD
    current_time = now.strftime("%I:%M%p")  # Format: HH:MMam/pm

    cmd.execute("insert into alert values (null,'"+current_date+"','"+current_time+"','"+location+"','"+alert+"','"+lid+"')")

    con.commit()

    return {"message": "Alert sent successfully!"}
@flow.route("/checkotp",methods=['post','get'])
def checkotp():
    email = request.args.get("email")
    print(email)
    otp=request.args.get("otp")
    cmd.execute("SELECT otp,login_id FROM login WHERE email='"+email+"'")
    s=cmd.fetchone()
    otp_value = s[0]
    lid=s[1]

    if otp==otp_value:
        password=request.args.get("password")
        cmd.execute("UPDATE login SET password='"+password+"' WHERE login_id='"+str(lid)+"'")
        con.commit()
        return jsonify({'status': 'sucess', 'message': 'Success'})
    else:
        return jsonify({'status': 'error', 'message': 'Incorrect OTP'})


@flow.route("/forgot_password", methods=['POST'])
def forgot_password():
    # email = request.json.get('email')
    import random
    list_of_chars1 = "2345698"

    # inside your function
    otp = "11"
    length1 = 3
    for _ in range(length1):
        otp += random.choice(list_of_chars1)

    mymail = request.args.get('email')
    print(mymail)# Fetch the email address
    cmd.execute("SELECT * FROM login WHERE email='"+mymail+"'")
    result=cmd.fetchone()
    print(result)
    if result:
        # mymail='anjuraj118@gmail.com'


        try:
                    gmail = smtplib.SMTP('smtp.gmail.com', 587)
                    gmail.ehlo()
                    gmail.starttls()
                    gmail.login('kaswathi036@gmail.com', 'zboc nllq pnja zmwp')

                    msg = MIMEText("Your otp number is: " + otp)
                    msg['Subject'] = 'otp'
                    msg['To'] = mymail
                    msg['From'] = 'www.kaswathi036@gmail.com'

                    gmail.send_message(msg)
                    gmail.quit()
                    cmd.execute("UPDATE login SET otp='"+otp+"'  WHERE email='"+mymail+"'")
                    con.commit()
                    return jsonify({'status': 'sucess', 'message': 'Success.'})
        except Exception as e:
                    print("Couldn't sendemail:",e)

                    return jsonify({'status': 'error', 'message': 'User notfound.'})
    else:
        return jsonify({'status': 'error', 'message': 'Incorrect Email.'})
@flow.route('/controljunctions',methods=['post','get'])
def controljunctions():
    data=request.json
    junction=data.get('junction')
    lid=data.get('lid')

    return jsonify({'status': 'sucess', 'message': 'Success.'})



flow.run(host='0.0.0.0',port=8000)


Flask-Based AI Traffic Management System with User Authentication & Real-Time Traffic Control

import smtplib
from email.mime.text import MIMEText

from flask import *
import pymysql as pymysql

flow= Flask(__name__)
flow.secret_key = "abc"
con = pymysql.connect(host="localhost", user="root", password="root", port=3306, db="smartsignalhub", charset="utf8")
cmd = con.cursor()
import functools
def login_required(func):
    @functools.wraps(func)
    def secure_function():
        if "lid" not in session:
            return redirect("/")
        return func()
    return secure_function


@flow.route('/logout')
def logout():
    session.clear()
    return redirect('/')



@flow.route('/')
def login():
    return render_template("login.html")
@flow.route('/logincheck', methods=['post'])
def logincheck():
    user = request.form['username']
    psd = request.form['password']
    cmd.execute("select * from `login` where email='" + user + "' and password='" + psd + "'")
    result = cmd.fetchone()
    if result is None:
        return '''<script>alert("INVALID USERNAME AND PASSWORD");window.location='/'</script>'''
    elif result[3] == "admin":
        session['lid'] = result[0]
        cmd.execute("SELECT `userreg`.*,`feedback`.* FROM `feedback` JOIN `userreg` WHERE `userreg`.`login_id`=`feedback`.`userid`")
        result=cmd.fetchall()
        cmd.execute("SELECT COUNT(*) AS requestcount FROM userreg JOIN login ON login.login_id = userreg.login_id WHERE login.type = 'user' OR login.type = 'emergency'")
        usercount = cmd.fetchone()[0]
        cmd.execute("SELECT COUNT(*) AS pending_count FROM userreg JOIN login ON login.login_id = userreg.login_id WHERE login.type = 'pending'")
        requestcount=cmd.fetchone()[0]
        cmd.execute("SELECT COUNT(*) AS rejected_count FROM userreg JOIN login ON login.login_id = userreg.login_id WHERE login.type = 'rejected'")
        rejected=cmd.fetchone()[0]
        cmd.execute("SELECT COUNT(*) AS emergency_count FROM userreg WHERE usertype = 'emergency'")
        emergencycount=cmd.fetchone()[0]
        cmd.execute("select feedback from feedback")
        feedback=cmd.fetchone()
        return render_template('index.html',value=result,usercount=usercount,requestcount=requestcount,rejected=rejected,emergencycount=emergencycount,feedback=feedback)
@flow.route('/index')
def index():
    cmd.execute(
        "SELECT `userreg`.*,`feedback`.* FROM `feedback` JOIN `userreg` WHERE `userreg`.`login_id`=`feedback`.`userid`")
    result = cmd.fetchall()
    cmd.execute("SELECT COUNT(*) AS requestcount FROM userreg JOIN login ON login.login_id = userreg.login_id WHERE login.type = 'user' OR login.type = 'emergency'")
    usercount=cmd.fetchone()[0]
    cmd.execute("SELECT COUNT(*) AS pending_count FROM userreg JOIN login ON login.login_id = userreg.login_id WHERE login.type = 'pending'")
    requestcount = cmd.fetchone()[0]
    cmd.execute("SELECT COUNT(*) AS rejected_count FROM userreg JOIN login ON login.login_id = userreg.login_id WHERE login.type = 'rejected'")
    rejected = cmd.fetchone()[0]
    cmd.execute("SELECT COUNT(*) FROM `login` JOIN `userreg` ON `login`.`login_id` = `userreg`.`login_id` WHERE `login`.`type` = 'emergency'")
    emergencycount = cmd.fetchone()[0]
    cmd.execute("select feedback from feedback")
    feedback = cmd.fetchone()[0]
    return render_template('index.html',value=result,usercount=usercount,requestcount=requestcount,rejected=rejected,emergencycount=emergencycount,feedback=feedback)

@flow.route('/users')
def users():
    return render_template("users.html")



@flow.route('/viewuser')
@login_required
def viewuser():
    cmd.execute("select userreg.*,login.type from `userreg` join login on  login.`login_id`=`userreg`.`login_id` where login.type='user' or login.type='emergency'")
    result=cmd.fetchall()
    return render_template("view_user.html",value=result)
@flow.route('/viewnewrequest')
@login_required
def viewnewrequest():
    cmd.execute("SELECT userreg.*, login.type FROM `userreg` JOIN `login` ON `login`.`login_id` = `userreg`.`login_id` WHERE login.type = 'pending'")
    result = cmd.fetchall()
    return render_template("newrequest.html", value=result)
@flow.route('/emergencyvehicles')
@login_required
def emergencyvehicles():
    cmd.execute("SELECT `login`.*,`userreg`.* FROM `login` JOIN `userreg` ON `login`.`login_id`=`userreg`.`login_id` WHERE login.`type`='emergency'")
    result=cmd.fetchall()
    return render_template('view_emergency.html',value=result)

@flow.route('/viewrejecteduser')
@login_required
def viewrejecteduser():
    cmd.execute("select userreg.*,login.type from `userreg` join login on  login.`login_id`=`userreg`.`login_id` where login.type='rejected' ")
    result=cmd.fetchall()
    return render_template("rejecteduserview.html",value=result)
@flow.route('/newrequestconfirm')
@login_required
def newrequestconfirm():
    usertype = request.args.get("type")
    loginid = request.args.get("id")
    print(usertype)
    print(loginid)
    session['type']=usertype
    session['id']=loginid
    return render_template("newrequestconfirm.html")
@flow.route('/rejnewrequestconfirm')
@login_required
def rejnewrequestconfirm():
    usertype = request.args.get("type")
    loginid = request.args.get("id")
    print(usertype)
    print(loginid)
    session['type']=usertype
    session['id']=loginid
    return render_template("rejectnewrequestconfirm.html")
@flow.route('/acceptuser',methods=['post'])
@login_required
def acceptuser():
    usertype=session["type"]
    loginid=session["id"]
    cmd.execute("UPDATE login JOIN userreg ON login.`login_id`=`userreg`.`login_id` SET login.`type`='"+usertype+"' WHERE userreg.`usertype`='"+usertype+"' AND `login`.`login_id`='"+loginid+"' ")
    con.commit()
    return '''<script>alert("Accepted Succesfully");window.location='/index'</script>'''
@flow.route('/rejectuser',methods=['post'])
@login_required
def rejectuser():
    type=session['type']
    print(type,'****************')

    loginid=session["id"]
    print(loginid,'***********')
    cmd.execute("UPDATE login JOIN userreg ON login.`login_id`=`userreg`.`login_id` SET login.`type`='rejected'  WHERE  `login`.`login_id`='"+loginid+"'AND userreg.`usertype`='"+type+"'")
    con.commit()
    return '''<script>alert("rejected Sucessfully");window.location='/index'</script>'''
@flow.route('/viewtraffic')
@login_required
def viewtraffic():
    cmd.execute("""
    SELECT `trafficcontrol`.*, `userreg`.* 
    FROM `trafficcontrol` 
    JOIN `userreg` 
        ON `trafficcontrol`.`login_id` = `userreg`.`login_id`
    """)
    res = cmd.fetchall()
    print(res)
    return render_template("viewtrafficcontrol.html", value=res)

@flow.route('/viewcongestion')
@login_required
def viewcongestion():
    cmd.execute("SELECT `congestion`.* FROM `congestion`")
    result=cmd.fetchall()
    return render_template("viewcongestion.html",value=result)
@flow.route('/suggestroute')
def suggestroute():
    conid=request.args.get("conid")
    session["congestionid"]=conid
    return render_template("suggestroute.html")
@flow.route('/updateroute',methods=['post'])
@login_required
def updateroute():

    conid=session["congestionid"]
    route=request.form["sroute"]
    cmd.execute("update congestion set suggested_route='"+route+"' where congestion_id='"+conid+"'")
    con.commit()
    return '''<script>alert(" SUCCESS");window.location='/viewcongestion'</script>'''
@flow.route('/alert')
@login_required
def alert():
    cmd.execute("SELECT `alert`.*, `userreg`.* FROM `alert` JOIN `userreg` ON `alert`.`loginid` = `userreg`.`login_id` ORDER BY `alert`.`date` DESC LIMIT 1")
    res=cmd.fetchone()

    return render_template("alert.html",value=res)



flow.run(debug=True)
