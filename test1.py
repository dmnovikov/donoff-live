import sqlite3
from datetime import datetime, timezone
from dateutil import parser

connection = sqlite3.connect('live.db')

cursor = connection.cursor()


i_user='u1'
i_dev='h1'
i_last_seen=datetime.now(timezone.utc)

def update_last_seen(input_user, input_dev, input_last_seen):
    cursor.execute("SELECT * from live where user=? and dev=?",(input_user, input_dev))
    data=cursor.fetchone()
    if data:
        print ("found, update ", input_last_seen)
        print ("id=",data[0])
        cursor.execute("UPDATE live SET last_seen=? WHERE id=?", (input_last_seen, data[0]))

    else:
        print ("not found, insert")
        cursor.execute("insert into live (user,dev,last_seen) values (?,?,?)",(input_user, input_dev, input_last_seen))


update_last_seen(i_user, i_dev, i_last_seen)
# update_last_seen(i_user, 'h3', i_last_seen)
# update_last_seen(i_user, 'h3', '1111')

cursor.execute("SELECT last_seen from live where id=1")
connection.commit()


print ("NOW:",datetime.now(timezone.utc))

date_str=cursor.fetchone()[0]
#datetime_object = datetime.strptime(date_str)

res=parser.parse(date_str)

print("date from base",res.date())
print("date-time from base",res.strftime("%Y-%m-%d %H:%M:%S"))