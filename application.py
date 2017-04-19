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
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        get_all = "SELECT * from `user`"
        cur.execute(get_all)
        data = cur.fetchall()
        conn.commit()
        return json.dumps({"items":data})

@route('/meetingrooms', method='GET')
def get_rooms():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        date1 = '\''+request.query.get('from_date')+'\''
        date2 = '\''+request.query.get('to_date')+'\''
        print date1
        print date2
        rooms = '''SELECT * from `meeting_locations` where `id` not in (select `location_id` from `meeting` where `id` = (select `meeting_id` from `room_booking` where (`from_date` <= %s and `to_date` >= %s) OR (`from_date` <= %s and  (`to_date` <= %s and `to_date` >= `from_date`)) OR (`from_date` >= %s and `to_date` <= %s) OR ((`from_date` >= %s and `from_date` <= `to_date`) and `to_date` >= %s)))'''
        print "ROOMS:", rooms % (date1, date2, date1, date2, date1, date2, date1, date2)
        cur.execute(rooms, (date1, date2, date1, date2, date1, date2, date1, date2))
        result = cur.fetchall()
        conn.commit()
        return json.dumps({"items":result})

@route('/meetings', method='GET')
def get_meetings():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        username = request.query.get('username')
        meetings = "SELECT `id`, `name` from meeting where `id` in (select `meeting_id` from `meeting_participant` where `user_name` = %s)"
        cur.execute(meetings, (username))
        result = cur.fetchall()
        conn.commit()
        return json.dumps({"items":result})

@route('/meeting', method='GET')
def get_meetings():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        meeting_id = request.query.get('meeting_id')
        meetings = "SELECT `creator`, `name` from meeting where `id` = %s"
        print (meetings % (meeting_id))
        cur.execute(meetings, (meeting_id))
        result = cur.fetchall()
        conn.commit()
        return json.dumps({"items":result})

@route('/meeting', method='POST')
def create_meeting():
    with conn.cursor() as cur:
        name = request.forms.get('name')
        creator = request.forms.get('creator')
        location_id = request.forms.get('location_id')
        from_date = request.forms.get('from_date')
        to_date = request.forms.get('to_date')
        print name, creator, location_id, from_date, to_date
        meeting = "INSERT INTO `meeting` (`name`, `creator`, `location_id`) values (%s, %s, %s)"
        cur.execute(meeting, (name, creator, location_id))
        meeting_id = cur.lastrowid
        book = "INSERT INTO `room_booking` (`meeting_id`, `from_date`, `to_date`) values (%s, %s, %s)"
        cur.execute(book, (meeting_id, from_date, to_date))
        participant = "INSERT INTO `meeting_participant` values(%s, %s)"
        cur.execute(participant, (meeting_id, creator))
        conn.commit()

@route('/participants', method='POST')
def add_participants():
    with conn.cursor() as cur:
        meeting_id = request.forms.get('meeting_id')
        participants = request.forms.get('participants')
        insert = "INSERT INTO `meeting_participant` (`meeting_id`, `user_name`) values (%s, %s)"
        participants = participants[1:-1].split(', ')
        for p in participants:
            cur.execute(insert, (meeting_id, p))
        conn.commit()

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
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        username = request.forms.get('username')
        note_title = request.forms.get('note_title')
        note_text = request.forms.get('note_text')
        email = request.forms.get('email')
        insert = "INSERT INTO `notes` (`username`, `timestamp`, `note_title`, `note_text`, `email`) values (%s, %s, %s, %s, %s)"
        cur.execute(insert, (username, timestamp, note_title, note_text, email))

        conn.commit()

@route("/allpolls", method='GET')
def all_polls():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        username = request.query.get('username')
        poll = "SELECT `id`, `question` from `polls` where `status` = %s and `meeting_id` in (select `meeting_id` from `meeting_participant` where `username` = %s)"
        cur.execute(poll, (True, username))
        data = cur.fetchall()
        conn.commit()
        return json.dumps({"items":data})

@route("/getpoll", method='GET')
def get_poll():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        poll_id = request.query.get('poll_id')
        poll = "SELECT `id`, `question`, `count_option1`, `count_option2`, `count_option3`, `count_option4` from `polls` where `id` = %s"
        cur.execute(poll, (poll_id))
        data = cur.fetchall()
        conn.commit()
        return json.dumps({"items":data})

@route("/token", method='POST')
def create_token():
    with conn.cursor() as cur:
        token_id = request.forms.get('token_id')
        username = request.forms.get('username')
        insert = "INSERT INTO `tokens` (`token_id`, `username`) values(%s, %s)"
        cur.execute(insert, (token_id, username))
        conn.commit()

@route("/submitpoll", method='POST')
def submit_poll():
    with conn.cursor() as cur:
        poll_id = request.forms.get('poll_id')
        username = request.forms.get('username')
        option = 'count_option'+request.forms.get('option')
        insert = "UPDATE `polls` set %s = %s + 1 where `id` = %s"
        cur.execute(insert, (option, option, poll_id))
        conn.commit()

@route("/polls", method='POST')
def create_poll():
    with conn.cursor() as cur:
        meeting_id = request.forms.get('meeting_id')
        username = request.forms.get('username')
        question = request.forms.get('question')
        option1 = request.forms.get('option1')
        option2 = request.forms.get('option2')
        option3 = request.forms.get('option3')
        option4 = request.forms.get('option4')
        status = True
        poll = "INSERT INTO `polls` (`username`, `meeting_id`, `question`, `option1`, `option2`, `option3`, `option4`, `status`, `count_option1`, `count_option2`, `count_option3`, `count_option4`) values (%s, %s, %s, %s, %s, %s, %s, %s, 0, 0, 0, 0)"
        cur.execute(poll, (username, meeting_id, question, option1, option2, option3, option4, status))
        conn.commit()

@route("/note", method='GET')
def get_note():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        get_all = "SELECT id, username, note_title, note_text, email from `notes` where `username` = %s"
        username = request.query.get('username')
        cur.execute(get_all, (username))
        data = cur.fetchall()
        return json.dumps({"items":data})


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
        return json.dumps({"items": [{"username": username, "password": password, "status": res}] })

application = bottle.default_app()
if __name__ == "__main__":
    run(host='0.0.0.0', port=8080, debug=True)
