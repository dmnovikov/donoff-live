import paho.mqtt.client as mqtt
from datetime import datetime, timezone
import smtplib
import json
import sqlite3
import re

from apscheduler.schedulers.background import BackgroundScheduler

from configparser import ConfigParser

import time
import logging

TOPIC_SEMDMAIL = "/sys/sendmail"
TOPIC_SENSOR_BASELOG = "/sys/sensor_baselog"
TOPIC_ALIVE = "/sys/alive"
TOPICS_UPTIME="/donoff/+/out/time_up"
TOPICS_TEMP_IN="/donoff/+/out/temp_in"
TOPICS_TEMP_OUT="/donoff/+/out/temp_out"
TOPICS_LOG="/donoff/+/out/log"
TOPICS_INFO="/donoff/+/out/info"
TOPICS_RELAYS1="/donoff/+/out/b1"
TOPICS_RELAYS2="/donoff/+/out/b2"
TOPICS_SCT01="/donoff/+/out/sct013_1"
TOPICS_SCT02="/donoff/+/out/sct013_2"
TOPICS_SCT03="/donoff/+/out/sct013_3"
TOPICS_SCT_3ph="/donoff/+/out/sct013x3"


#logging.basicConfig()

# global database_connected
database_connected = False
mqtt_connected = False


# global conn

def debug(_subj, _message):
    print(_subj + ":" + _message)
    pass


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    global mqtt_connected

    if rc != 0:
        mqtt_connected = False
        return

    mqtt_connected = True

    debug("SYS", str("Connected with result code " + str(rc)))
    # client.subscribe("/donoff/b1/out/info")
    dt = datetime.now(timezone.utc)
    s_time_command = "time=" + str(dt.hour) + ":" + str(dt.minute)
    # print("D:"+s_time_command);
    # ret=client.publish("/donoff/b1/in/params", s_time_command);

    # client.subscribe(TOPIC_SEMDMAIL)
    # client.subscribe(TOPIC_SENSOR_BASELOG)
    # client.subscribe(TOPIC_ALIVE)

    client.subscribe(TOPICS_UPTIME)
    client.subscribe(TOPICS_TEMP_IN)
    client.subscribe(TOPICS_TEMP_OUT)
    client.subscribe(TOPICS_LOG)
    client.subscribe(TOPICS_INFO)
    client.subscribe(TOPICS_RELAYS1)
    client.subscribe(TOPICS_RELAYS2)
    client.subscribe(TOPICS_SCT01)
    client.subscribe(TOPICS_SCT02)
    client.subscribe(TOPICS_SCT03)
    client.subscribe(TOPICS_SCT_3ph)
    


def on_disconnect(client, userdata, rc):
    debug("MQTTDISCONNECT", "DISCONNECT")
    global mqtt_connected
    mqtt_connected = False


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #print(msg.topic + "-->" + str(msg.payload))
    global conn

    if msg.retain == 1:
        debug("MQTTPARSER", "Skip retain message")
        return

    curs=conn.cursor()
    dt=datetime.now()
    topic_data = msg.topic.split("/")
    t_user=topic_data[1]
    t_dev=topic_data[2]
    dt=datetime.now()
    msg_decoded = msg.payload.decode("utf-8")
        

    if re.search('/donoff/.+/out/time_up',msg.topic):
      
        curs.execute("SELECT * from live where user=? and dev=?",(t_user,t_dev))        
        data=curs.fetchone()

        if data:
            #print ("found, update")
            curs.execute("UPDATE live SET last_seen=?, time_up=? WHERE id=?", (dt, msg_decoded, data[0]))

        else:
            #print ("not found, insert")
            curs.execute("insert into live (user,dev,last_seen, time_up) values (?,?,?,?)",(t_user, t_dev, dt, msg_decoded))

    if re.search('/donoff/.+/out/temp_in',msg.topic):

        sensor_val=int (float(msg_decoded)*100)
        curs.execute("insert into sensors_in (user,dev,time, type, mult, value) \
            values (?,?,?,?,?,?)",(t_user, t_dev, dt, 0, 100, sensor_val))

        #curs.execute("insert into sensors_all (dev_id, time, type, name, mult, value) \
        #            values ((select id from live where user=? and dev=?), ?, ?, ?,?,?)", \
        #            (t_user, t_dev,dt, 0, 't_in', 100, sensor_val))
    
    if re.search('/donoff/.+/out/temp_out',msg.topic):

        sensor_val=int (float(msg_decoded)*100)
        curs.execute("insert into sensors_out (user,dev,time, type, mult, value) \
            values (?,?,?,?,?,?)",(t_user, t_dev, dt, 0, 100, sensor_val))

        #curs.execute("insert into sensors_all (dev_id, time, type, name, mult, value) \
        #            values ((select id from live where user=? and dev=?), ?, ?, ?,?,?)", \
        #            (t_user, t_dev,dt, 0, 't_out', 100, sensor_val))

    if re.search('/donoff/.+/out/log',msg.topic) or re.search('/donoff/.+/out/info',msg.topic):

        debug("LOG", "TOPIC=" + msg.topic+" MSG="+msg_decoded)

        expr1=re.match('[^:]*=.+', msg_decoded) #all messgaes as val=value

        if expr1:
            type_txt='show value'
            type_i=0
            msg=msg_decoded
            print('show value  detected')

        exprN=re.match('N:(.*)=(.+)', msg_decoded) 

        if exprN and not expr1:
            type_txt='new value'
            type_i=1 #new val
            print('N: detected')
            msg=exprN.group(1)+'='+exprN.group(2)
            debug('LOG', "N:detected->"+exprN.group(1)+':=:'+ exprN.group(2))

        exprI=re.match(r'I:(.+)', msg_decoded) 
        
        if exprI and not expr1:
            type_txt='info msg'
            type_i=2 #info
            msg=exprI.group(1)
        
            #print('I: detected')
            debug('LOG', "I:detected->"+exprI.group(1))
        
        exprSaved=re.match(r'N:\s([Ss]aved)', msg_decoded) 
        
        if exprSaved and not expr1:
            type_txt='eeprom saved'
            type_i=11 #saved
            msg=exprSaved.group(1)
            #print('Saved: detected')
            debug('LOG', "Saved:detected->"+exprSaved.group(1))

        exprE=re.match(r'E:(.+)', msg_decoded) 

        if exprE and not expr1:
            type_txt='error'
            type_i=3 #error
            msg=exprE.group(1)
            #print('I: detected')
            debug('LOG', "E:detected->"+exprE.group(1))

        exprGrp1=None


        if expr1 or exprE or exprI or exprN or exprSaved:
            curs.execute("insert into logging (user,dev,time, type_txt, type, msg) values (?,?,?,?,?,?)", (t_user, t_dev, dt, type_txt, type_i, msg))
            exprGrp1=1
        
        if exprGrp1 is None:
       
            exprL=re.match(r'^L:(.+)', msg_decoded) 
            print('begin L:')
            if exprL:
                exprOnOff=re.match(r'^(.+):([^,]+),(.+)$', exprL.group(1))
                print('begin LONOFF:')
                if exprOnOff:
                    src=exprOnOff.group(1)
                    event=0
                    if re.match(r'^[oO][Nn]$', exprOnOff.group(2)):
                        event=1
                    if re.match(r'^[oO][Ff][Ff]$', exprOnOff.group(2)):
                        event=2
                    msg=exprOnOff.group(3)
                    debug('LOG', 'src='+src+' event='+str(event)+' msg='+msg)
                    curs.execute("insert into log_onoff (user,dev,time, event, src, msg) values (?,?,?,?,?,?)", (t_user, t_dev, dt, event, src, msg))
                  

    if re.search('/donoff/.+/out/b.+',msg.topic):
        expr_relays=re.match(r'/donoff/.+/out/(b.+)', msg.topic)
        rname=expr_relays.group(1)
        if rname=='b1': rname='r1'
        if rname=='b2': rname='r2'

        state=int(msg_decoded)
        
        state=1
        #print ("relay log", "rname=", rname, " dev=", t_dev, " rname=", rname, " msg=", msg_decoded, " state=", state)
        #logging.debug("relay log", "rname=", rname)
        
        # curs.execute("insert into log_relays (dev_id, time, rname, state) \
        #             values ((select id from live where user=? and dev=?), ?, ?, ?)", \
        #             (t_user, t_dev,dt, rname, msg_decoded))

        curs.execute("insert into log_relays_ud (user,dev, time, rname, state) \
                    values (?,?, ?, ?, ?)", \
                    (t_user, t_dev, dt, rname, msg_decoded))
        pass

    if re.search('/donoff/.+/out/sct013.+',msg.topic):
        expr_relays=re.match(r'/donoff/.+/out/(sct013.+)', msg.topic)
        rname=expr_relays.group(1)
        sensor_val=int (float(msg_decoded)*100)
        
        #print ("relay log", "rname=", rname, " dev=", t_dev, " rname=", rname, " msg=", msg_decoded, " sensorval=", sensor_val)
        curs.execute("insert into sensors (user,dev,time, type, name, mult, value) \
            values (?,?,?,?,?,?,?)",(t_user, t_dev, dt, 1, rname, 100, sensor_val))


        
        pass

            



        # elif re.search('N:(.*)=(.+)', msg_decoded): #all messgaes as N:val=value
        #     m=re.match('N:(.*)=(.+)', msg_decoded)
        #     type_li=0 #info
        #     type_txt='new value'
        #     type=1 #log
        #     msg=msg_decoded
        #     print('N: detected')
        #     if m:
        #         debug('LOG', "N:detected"+m.group(1)+':::'+ m.group(2))




       
        #curs.execute("insert into logging (user,dev,time, type, mult, value) 
        #values (?,?,?,?,?,?)",(topic_data[1], topic_data[2], dt, 0, 100, sensor_val))


        


def on_log(mosq, obj, mid, string):

    if re.search('Caught exception', string):
        print("Log: " + str(string))

    # if not re.search(r'Received PUBLISH', string):
    #     print("Log: " + str(string))

    pass


def on_publish(mosq, obj, mid):  # create function for callback
    # print("mid: " + str(mid))
    pass


def tick():
    _str = ''
    if mqtt_connected:
        _str += "MQTT OK"
    else:
        _str += "MQTT DISCONNECTED"

    _str += ", "
    if database_connected:
        _str += "DATABASE OK"
    else:
        _str += "DATABASE DISCONNECTED"

    debug("TICK", _str)
    debug("TICK", "db commit")
    conn.commit()


def connect_sql_lite_database(file_db):
    connection = sqlite3.connect(file_db, check_same_thread=False)
    return connection


# def reconnect_base():
#     # print('*************** Base connection OK')
#     global conn
#     global database_connected
#     if not conn:
#         debug("SYS", 'Try reconnect to database ...')
#         database_connected = False
#         conn = connect_database()
#         if conn:
#             debug("SYS", 'Database conn OK ...')
#             database_connected = True


def reconnect_mqtt():
    # global client
    # if not (client.isConnected() ):
    #     debug("SYS", "MQTT NOT connected")
    if mqtt_connected:
        debug("SYS", "MQTT OK")
    else:
        debug("SYS", "MQTT NOT Connected")
    pass


def reconnect():
    #reconnect_base()
    reconnect_mqtt()

def update_last_seen(cursor, input_user, input_dev, input_last_seen):
    debug("SYS", "enter last seen")
    cursor.execute("SELECT * from live where user=? and dev=?",(input_user, input_dev))
    data=cursor.fetchone()
    print ("data=", data[0])
    if data:
        print ("found, update")
        print ("id=",data[0])
        cursor.execute("UPDATE live SET last_seen=? WHERE id=?", (input_last_seen, data[0]))

    else:
        print ("not found, insert")
        cursor.execute("insert into live (user,dev,last_seen) values (?,?,?)",(input_user, input_dev, input_last_seen))

    print ("db commit")
    conn.commit()


data_file = 'conf.donoff'

debug('SYS', 'Starting Donoff python broker')

config = ConfigParser()
config.read(data_file)

try:
    mqtt_conf = config['mqtt']
    email_conf = config['email']
    sql_conf = config['sql']
    sql_lite= config['sql_lite']

    gmail_login = email_conf['gmail_login']
    gmail_pass = email_conf['gmail_pass']
    from_str = email_conf['from_str']

    DBNAME = sql_conf['name']
    DBUSER = sql_conf['user']
    DBPASS = sql_conf['pass']
    DBHOST = sql_conf['host']
    DBPORT = sql_conf['port']

    mqtt_login = mqtt_conf['login']
    mqtt_pass = mqtt_conf['password']
    mqtt_server = mqtt_conf['server']
    mqtt_port = mqtt_conf['port']

    file_db=sql_lite['filename']

except KeyError:
    debug("SYS", "Error config file")
    raise SystemExit(1)

print ("file_db=", file_db)
conn = connect_sql_lite_database('live.db')

if conn:
    database_connected = True
    debug("SYS","database connect ok")
    # cursor=conn.cursor()
    # cursor.execute("SELECT * from live ")
    # data=cursor.fetchone()
    # print ("data=", data)

else:
    debug("SYS","database ERROR")


client = mqtt.Client("mypython")
client.username_pw_set(username=mqtt_login, password=mqtt_pass)

client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.on_log = on_log
client.on_publish = on_publish

try:
    debug("SYS", 'Connecting to server=' + str(mqtt_server) + ' port=' + str(mqtt_port) + ' login=' + str(
        mqtt_login) + ' pass=' + mqtt_pass)
    client.connect(mqtt_server, port=int(mqtt_port), keepalive=10)
    mqtt_connected = True
    debug("SYS", "MQTT connected OK")
except:
    mqtt_connected = False
    debug("SYS", "MQTT connected FALSE")

client.loop_start()
scheduler = BackgroundScheduler()
scheduler.add_job(tick, 'interval', seconds=10)
scheduler.add_job(reconnect, 'interval', seconds=30)
scheduler.start()

while True:
    # print("publish")
    time.sleep(1)  # sleep for 10 seconds before next call
