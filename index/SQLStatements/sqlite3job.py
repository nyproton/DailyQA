import sqlite3
import numpy as np
import io
from DailyQARecord import DailyQARecord
import pandas as pd
import os

def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())


def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)


def createTable():

    sqlite3.register_adapter(np.ndarray, adapt_array)

    sqlite3.register_converter("array", convert_array)

    ######### Create Table ############
    with open('CreateTable.sql', 'r') as f:
        conn = sqlite3.connect('../DailyQA.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cur = conn.cursor()
        cur.execute('drop table if exists DailyQARecord')
        conn.commit()
        cur.execute(f.read())
        conn.commit()
        conn.close()


def addRecord(opgfile, room):
    sqlite3.register_adapter(np.ndarray, adapt_array)

    sqlite3.register_converter("array", convert_array)

    qa = DailyQARecord.CreateFromFile(opgfile, room)
    spotQAdf = pd.DataFrame(qa.spotQA)
    XOfflist = ';'.join([str(i) for i in spotQAdf.XOff])
    YOfflist = ';'.join([str(i) for i in spotQAdf.YOff])
    XSigmaList = ';'.join([str(i) for i in spotQAdf.XSigma])
    YSigmaList = ';'.join([str(i) for i in spotQAdf.YSigma])
    conn = sqlite3.connect('../DailyQA.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cur = conn.cursor()
    qry = 'insert into DailyQARecord ('
    qry += 'therapist, createDate, room, doorWarning, doorInterlock, intercom, videoMonitor, '
    qry += 'searchButton, radiationMonitor, beamPause, safetyCheck, panelA, panelB, '
    qry += 'CBCTA, CBCTB, imageCheck, laserSI, laserRL, laserAP, laserCheck, xa, ya, doseArray, calculated, excluded, '
    qry += 'energies, fieldSizeX, fieldSizeY, leftPenumbra, '
    qry += 'rightPenumbra, upPenumbra, downPenumbra, flatnessX, flatnessY, '
    qry += 'symmetryX, symmetryY, outputPass, energyPass, spotPositionXPass, '
    qry += 'spotPositionYPass, spotPositionCheck, spotSizeXPass, spotSizeYPass, '
    qry += 'spotSizeCheck, background, output, energy, spotXOff, spotYOff, '
    qry += 'spotXSigma, spotYSigma, note) values ('
    qry += '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '
    qry += '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '
    qry += '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    cur.execute(qry,
                (qa.therapist, qa.reportDate, qa.room, qa.doorWarning, qa.doorInterlock, qa.intercom, qa.videoMonitor,
                 qa.searchButton, qa.radiationMonitor, qa.beamPause, qa.safetyCheck, qa.panelA, qa.panelB,
                 qa.CBCTA, qa.CBCTB, qa.imageCheck, qa.laserSI, qa.laserRL, qa.laserAP, qa.laserCheck, qa.xa, qa.ya, qa.doseArray, True, False,
                 ';'.join([str(i) for i in qa.energies]), qa.profileQA[0][2], qa.profileQA[1][2], qa.profileQA[0][0],
                 qa.profileQA[0][1], qa.profileQA[1][1], qa.profileQA[1][0], qa.profileQA[0][3], qa.profileQA[1][3],
                 qa.profileQA[0][4], qa.profileQA[1][4], qa.outputPass, qa.energyPass, ';'.join(qa.spotPositionXPass),
                 ';'.join(qa.spotPositionYPass), qa.spotPositionCheck, ';'.join(qa.spotSizeXPass), ';'.join(qa.spotSizeYPass),
                 qa.spotSizeCheck, qa.background, qa.output, qa.energy, XOfflist, YOfflist, XSigmaList, YSigmaList, qa.note))
    conn.commit()
    conn.close()


def test():
    sqlite3.register_adapter(np.ndarray, adapt_array)

    sqlite3.register_converter("array", convert_array)
    # conn = sqlite3.connect('../DailyQA.db', detect_types=sqlite3.PARSE_DECLTYPES)
    conn = sqlite3.connect('../DailyQA.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT * FROM DailyQARecord')
    data = cur.fetchone()
    print(data)


def draw():
    d = pd.bdate_range(start='', end='')

#  x, y = list(map(float, s.split(b";"))) # examples of %f;%f reverse

createTable()
# # fname = r'../uploads/Integral 0019.opg'
# flist = os.listdir(r'../uploads/standard')
# for f in flist:
#     fname = os.path.join(r'../uploads/standard', f)
#     if 'TR2' in f:
#         addRecord(fname, 'TR2')
#         print('Add QA record {} to database'.format(fname))
#     elif 'TR3' in f:
#         addRecord(fname, 'TR3')
#         print('Add QA record {} to database'.format(fname))
#
# # test()
