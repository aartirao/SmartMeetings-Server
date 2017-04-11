from bottle import route, run, request
import bottle
import json
import time
import datetime

import pymysql
conn = None

try:
    conn = pymysql.connect(db='smartmeetingdb', user='group30', host='smartmeeting.cyrypi4sn74l.us-west-2.rds.amazonaws.com', passwd='12345678')
except:
    print "I am unable to connect to the database"



@route('/home')
def home():
    return "Smart Meetings!"

@route('/user', method='POST')
def create_user():
    with conn.cursor() as cur:
        insert = "INSERT into `user` (`username`, `password`, `name`, `email`, `phone`) values (%s, %s, %s, %s, %s)"
        username = request.forms.get('username')
        password = request.forms.get('password')
        name = request.forms.get('name')
        email = request.forms.get('email')
        phone = request.forms.get('phone')
        cur.execute(insert, (username, password, name, email, phone))
        conn.commit()

@route('/users', method='GET')
def get_users():
    with conn.cursor() as cur:
        get_all = "SELECT * from `user`"
        cur.execute(get_all)
        data = cur.fetchall()
        data = json.dumps(data)
        conn.commit()
        print data
        return data

@route('/location', method='POST')
def save_location():
    with conn.cursor() as cur:
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        username = request.forms.get('username')
        latitude = request.forms.get('latitude')
        longitude = request.forms.get('longitude')
        print username, latitude, longitude
        insert = "INSERT INTO `location_history` (`username`, `latitude`, `longitude`, `timestamp`) values (%s, %s, %s, %s)"
        cur.execute(insert, (username, latitude, longitude, timestamp))
        conn.commit()

@route("/note", method='POST')
def save_note():
    with conn.cursor() as cur:
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        id_row = request.forms.get('id')
        username = request.forms.get('username')
        note_title = request.forms.get('note_title')
        note_text = request.forms.get('note_text')
        if id_row == None:
            insert = "INSERT INTO `notes` (`username`, `timestamp`, `note_title`, `note_text`) values (%s, %s, %s, %s)"
            cur.execute(insert, (username, timestamp, note_title, note_text))
        else:
            update = "UPDATE `notes` SET `note_text` = %s where id = %s"
            cur.execute(update, (note_text, id_row))
        conn.commit()

@route("/note", method='GET')
def get_note():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        get_all = "SELECT id, username, note_title, note_text from `notes` where `username` = %s"
        username = request.query.get('username')
        cur.execute(get_all, (username)) 
        data = cur.fetchall()        
        return json.dumps(data)
        

@route('/auth', method='GET')
def auth():
    with conn.cursor() as cur:
        get = "SELECT username FROM `user` where `username` = %s and `password` = %s"
        username = request.query.get('username')
        password = request.query.get('password')
        cur.execute(get, (username, password))
        data = cur.fetchall()
        res = False
        if (len(data) > 0):
            res = True
        return json.dumps(res)


@route('/poll', method='POST')
def create_poll():
  with conn.cursor() as cur:
    username = request.forms.get('username')
    question_text = request.forms.get('question_text')
    option_1 = request.forms.get('option_1')
    option_2 = request.forms.get('option_2')
    option_3 = request.forms.get('option_3')
    option_4 = request.forms.get('option_4')
    insert = "INSERT INTO `poll_questions` (`username`, `question_text`, `option_1`, `option_2`, `option_3`, `option_4`) values (%s, %s, %s, %s)"
    cur.execute(insert, (username, question_text, option_1, option_2, option_3, option_4))
    conn.commit()

application = bottle.default_app()
if __name__ == "__main__":
    run(host='0.0.0.0', port=8080, debug=True)



