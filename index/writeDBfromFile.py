# this is a file to read file in upload folder and write it into a database, not for routine use

from DailyQARecord import DailyQARecord

import os

flist = os.listdir("uploads")
for fname in flist:
    room = 'NONE'
    if 'TR2' in fname:
        room = 'TR2'
    if 'TR3' in fname:
        room = 'TR3'
    if room != 'NONE':
        dailyQARecord = DailyQARecord.CreateFromFile(os.path.join('uploads', fname), room)
        dailyQARecord.writeToDB()
        print('{} is written to database.'.format(fname))