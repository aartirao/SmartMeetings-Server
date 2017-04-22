from bottle import route, run, request
from bson import json_util
from math import radians, cos, sin, asin, sqrt
from collections import Counter
import bottle
import json
import time
import datetime
import operator
from dateutil import parser

import pusher
pusher_client = pusher.Pusher("329265", "bdf3e36a58647e366f38", "a631bb96bd8a4b3c0e69")


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
def get_all_meetings():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        username = request.query.get('username')
        meetings = "SELECT `location`.`name` as `location_name`, `location`.`latitude`, `location`.`longitude`,  `m`.`id`, `m`.`name`, `m`.`creator`, `room`.`from_date`, `room`.`to_date` from `meeting` `m` join `room_booking` `room` join `meeting_locations` `location` on `m`.`id` = `room`.`meeting_id` and `m`.`location_id` = `location`.`id` where `m`.`id` = (select `meeting_id` from `meeting_participant` where `user_name` = %s)"
        cur.execute(meetings, (username))
        result = cur.fetchall()
        conn.commit()
        return json.dumps({"items":result}, default=date_handler)

def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj

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
        participants = request.forms.get('participants')
        print name, creator, location_id, from_date, to_date
        meeting = "INSERT INTO `meeting` (`name`, `creator`, `location_id`) values (%s, %s, %s)"
        cur.execute(meeting, (name, creator, location_id))
        meeting_id = cur.lastrowid
        book = "INSERT INTO `room_booking` (`meeting_id`, `from_date`, `to_date`) values (%s, %s, %s)"
        cur.execute(book, (meeting_id, from_date, to_date))
        participant = "INSERT INTO `meeting_participant` values(%s, %s)"
        cur.execute(participant, (meeting_id, creator))
        for p in participants.split(', '):
            cur.execute(participant, (meeting_id, p))
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
        poll = "SELECT * from `polls` where `status` = %s and `meeting_id` in (select `meeting_id` from `meeting_participant` where `user_name` = %s)"
        cur.execute(poll, (True, username))
        data = cur.fetchall()
        conn.commit()
        return json.dumps({"items":data})

@route("/getpoll", method='GET')
def get_poll():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        poll_id = request.query.get('poll_id')
        poll = "SELECT * from `polls` where `id` = %s"
        cur.execute(poll, (poll_id))
        data = cur.fetchall()
        conn.commit()
        return json.dumps({"items":data})

@route("/token", method='POST')
def create_token():
    with conn.cursor() as cur:
        token_id = request.forms.get('token_id')
        username = request.forms.get('username')
        insert = "INSERT IGNORE INTO `tokens` (`token_id`, `username`) values(%s, %s)"
        cur.execute(insert, (token_id, username, username))
        conn.commit()

@route("/submitpoll", method='POST')
def submit_poll():
    with conn.cursor() as cur:
        poll_id = request.forms.get('poll_id')
        username = request.forms.get('username')
        option = 'count_option'+request.forms.get('option')
        insert = "UPDATE `polls` set "+option+" = "+option+" + 1 where `id` = %s"
        cur.execute(insert, (poll_id))
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
        poll_id = cur.lastrowid
        notify_participants(meeting_id, question, poll_id, (option1, option2, option3, option4))

@route("/quickquestions", method='POST')
def quick_question():
    with conn.cursor() as cur:
        meeting_id = request.forms.get('meeting_id')
        username = request.forms.get('username')
        question = request.forms.get('question')
        query = "INSERT INTO `quick_question` (`question`, `meeting_id`, `creator`) values (%s, %s, %s)"
        cur.execute(query, (question, meeting_id, username))
        conn.commit()
        question_id = cur.lastrowid
        notify_questions(meeting_id, question, question_id)

@route("/submitquickquestion", method='POST')
def submit_answers():
    with conn.cursor() as cur:
        question_id = request.forms.get('question_id')
        answer = request.forms.get('answer')
        query = "INSERT INTO `question_answer` (`q_id`, `answer`) values (%s, %s)"
        cur.execute(query, (question_id, answer))
        conn.commit()

@route("/allquickquestions", method='GET')
def list_questions():
    data = []
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        username = request.query.get('username')
        query = "SELECT `id`, `question` from `quick_question` where `meeting_id` in (select `meeting_id` from `meeting_participant` where `user_name` = %s)"
        cur.execute(query, (username))
        result = cur.fetchall()
        for r in result:
            q_id = r['id']
            answer_query = "SELECT `answer` from `question_answer` where `q_id` = %s"
            cur.execute(answer_query, (q_id))
            answers = cur.fetchall()
            final_answers = (',').join(answer['answer'] for answer in answers)
            data.append({'question_id':q_id, 'question':r['question'],'answers':final_answers})
        return json.dumps({"items":data})

@route("/getlastlocation", method='GET')
def last_location():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        username = request.forms.get('username')
        query = "SELECT `latitude`, `longitude` from `location_history` where `username` = %s ORDER BY `id` DESC"
        cur.execute(query, (username))
        result = cur.fetchone()
        data = [{'latitude':result['latitude'], 'longitude':result['longitude']}]
        return json.dumps({"items":data})

@route("/checkclash", method='GET')
def check_clash():
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        participants = request.query.get('participants').split(",")
        from_date = request.query.get('from_date')
        print from_date
        from_date = parser.parse(from_date)
        to_date = request.query.get('to_date')
        print to_date
        to_date = parser.parse(to_date)
        for p in participants:
            p = p.strip()
            print p
            meeting_times = "SELECT `from_date`, `to_date` from `room_booking` where `meeting_id` = (select `meeting_id` from `meeting_participant` where `user_name` = %s LIMIT 1)"
            cur.execute(meeting_times, (p))
            user_meeting = cur.fetchall()
            for meet in user_meeting:
                user_from_date = meet['from_date']
                print user_from_date
                user_to_date = meet['to_date']
                print user_to_date
                if (user_from_date < from_date and user_to_date > to_date) or (user_from_date > from_date and user_to_date < to_date) or (user_from_date < from_date and user_to_date > from_date) or (user_from_date > from_date and user_from_date < to_date and user_to_date > to_date) :
                    return json.dumps({"items":[{'status':'false', 'result':'clashes with a participant'}]})
        return json.dumps({"items":[{'status':'true', 'location_list':median_location(participants)}]})

@route("/getlocations", method='GET')
def median_location(participants):
    data = []
    participants = request.query.get('participants').split(",")
    median_locations = {}
    latsum = 0
    longsum = 0
    total = len(participants)
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        query = "SELECT `latitude`, `longitude` from `location_history` where `username` = %s"
        for p in participants:
            p = p.strip()
            cur.execute(query, (p))
            latlong = cur.fetchall()
            locations = []
            for ll in latlong:
                locations.append(', '.join([str(ll["latitude"]), str(ll["longitude"])]))
            locations_to_count = (location for location in locations)
            c = Counter(locations_to_count)
            print "C", c
            median_locations[p] = c.most_common(1)[0][0]
        print median_locations
        for m in median_locations.values():
            latsum = latsum + float(m.split(", ")[0])
            longsum = longsum + float(m.split(", ")[1])
        #data.append({'location_list':find_optimal_location(latsum/total, longsum/total)})
        #return json.dumps({"items":data})
        return find_optimal_location(latsum/total, longsum/total)


def find_optimal_location(latitude, longitude):
    print latitude, longitude
    query = "SELECT `id`, `name`, `latitude`, `longitude` from `meeting_locations`"
    locations = {}
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(query)
        location_list = cur.fetchall()
        for location in location_list:
            lat = float(location["latitude"])
            longit = float(location["longitude"])
            locations[(',').join([str(location["id"]),location["name"]])] = haversine(longit, lat, longitude, latitude)
        print locations
        sorted_locations = sorted(locations.items(), key=operator.itemgetter(1))
        return list(s[0] for s in sorted_locations)


def haversine(lon1, lat1, lon2, lat2):
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return c

def notify_participants(meeting_id, question, poll_id, options):
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        token_list = []
        query = "SELECT `token_id` from `tokens` where `username` in (select `user_name` from `meeting_participant` where `meeting_id` = %s)"
        cur.execute(query, (meeting_id))
        tokens = cur.fetchall()
        for t in tokens:
            token_list.append(t['token_id'])
        print token_list
        pusher_client.notify(['polls'], {
          'fcm': {
            'registration_ids': token_list,
            'data': {
                "poll_id": poll_id,
                "question": question,
                "option1": options[0],
                "option2": options[1],
                "option3": options[2],
                "option4": options[3]
            },
            'notification': {
              'title': 'New poll!',
              'body': question,
              'click_action': "mc.asu.edu.smartmeetings.TARGET_NOTIFICATION"
            }
          },
          'webhook_url': 'http://requestb.in/1f7u53z1',
          'webhook_level': 'DEBUG'
        })

def notify_questions(meeting_id, question, question_id):
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        token_list = []
        query = "SELECT `token_id` from `tokens` where `username` in (select `user_name` from `meeting_participant` where `meeting_id` = %s)"
        cur.execute(query, (meeting_id))
        tokens = cur.fetchall()
        for t in tokens:
            token_list.append(t['token_id'])
        pusher_client.notify(['quickquestions'], {
          'fcm': {
            'registration_ids': token_list,
            'data': {
                "question_id": question_id,
                "question": question
            },
            'notification': {
              'title': 'Quick Question!',
              'body': question,
              'click_action': "mc.asu.edu.smartmeetings.TARGET_NOTIFICATION_QQ"
            }
          },
          'webhook_url': 'http://requestb.in/1f7u53z1',
          'webhook_level': 'DEBUG'
        })

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
