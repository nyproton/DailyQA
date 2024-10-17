import os
import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Frame, Spacer, Flowable, PageBreak, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

import io
from MatrixxUtil import opgread
from MorningQAAnalysis import checkBackground, checkSpot, checkProfile, checkOutput, checkEnergy, interp2d, \
    readBaseline, check
from DailyQAReport import getResults, getReport
from flask import current_app as app
from datetime import datetime

import pandas as pd
import sqlite3
import numpy as np

class DailyQARecord:



    def __init__(self, r, opgfile):

        # Basic Information
        self.room = r["room"]
        self.therapist = r["therapist"]

        # Mechanical and Safety
        self.safetyCheck = 'Pass'
        self.doorWarning = r["doorWarning"]
        if self.doorWarning != 'Pass':
            self.safetyCheck = 'Fail'
        self.doorInterlock = r["doorInterlock"]
        if self.doorInterlock != 'Pass':
            self.safetyCheck = 'Fail'
        self.intercom = r["intercom"]
        if self.intercom != 'Pass':
            self.safetyCheck = 'Fail'
        self.videoMonitor = r["videoMonitor"]
        if self.videoMonitor != 'Pass':
            self.safetyCheck = 'Fail'
        self.searchButton = r["searchButton"]
        if self.searchButton != 'Pass':
            self.safetyCheck = 'Fail'
        self.radiationMonitor = r["radiationMonitor"]
        if self.radiationMonitor != 'Pass':
            self.safetyCheck = 'Fail'
        self.beamPause = r["beamPause"]
        if self.beamPause != 'Pass':
            self.safetyCheck = 'Fail'
        self.collisionInterlock = r["collisionInterlock"]
        if self.collisionInterlock != 'Pass':
            self.safetyCheck = 'Fail'
        self.beamOnIndicator = r["beamOnIndicator"]
        if self.beamOnIndicator != 'Pass':
            self.safetyCheck = 'Fail'
        self.xrayOnIndicator = r["xrayOnIndicator"]
        if self.xrayOnIndicator != 'Pass':
            self.safetyCheck = 'Fail'



        # Image
        self.imageCheck = 'Pass'
        self.panelA = r["panelA"]
        if self.panelA != 'Pass':
            self.imageCheck = 'Fail'
        self.panelB = r["panelB"]
        if self.panelB != 'Pass':
            self.imageCheck = 'Fail'
        self.CBCTA = r["CBCTA"]
        if self.CBCTA != 'Pass':
            self.imageCheck = 'Fail'
        self.CBCTB = r["CBCTB"]
        if self.CBCTB != 'Pass':
            self.imageCheck = 'Fail'

        # Laser
        self.laserCheck = 'Pass'
        self.laserSI = r["laserSI"]
        if self.laserSI != 'Pass':
            self.laserCheck = 'Fail'
        self.laserRL = r["laserRL"]
        if self.laserRL != 'Pass':
            self.laserCheck = 'Fail'
        self.laserAP = r["laserAP"]
        if self.laserAP != 'Pass':
            self.laserCheck = 'Fail'

        # Matrixx

        # Baseline
        self.baseline = readBaseline(self.room)

        # Setup flag
        self.outputPass = 'Fail'
        self.energyPass = 'Fail'
        if 'outputLevel' in r:
            self.outputLevel = r['outputLevel']
        else:
            self.outputLevel = {'Fail': app.config.get('OUTPUT_FAIL'), 'Warning': app.config.get('OUTPUT_WARNING'), 'Relative': True}
        if 'energyLevel' in r:
            self.energyLevel = r['energyLevel']
        else:
            self.energyLevel = {'Fail': app.config.get('ENERGY_FAIL'), 'Warning': app.config.get('ENERGY_WARNING'), 'Relative': True}

        if 'spotPositionLevel' in r:
            self.spotPositionLevel = r['spotPositionLevel']
        else:
            self.spotPositionLevel = {'Fail': app.config.get('SPOT_POSITION_FAIL'), 'Warning': app.config.get('SPOT_POSITION_WARNING'), 'Relative': False}  # mm

        if 'spotSizeLevel' in r:
            self.spotSizeLevel = r['spotSizeLevel']
        else:
            self.spotSizeLevel = {'Fail': app.config.get('SPOT_SIZE_FAIL'), 'Warning': app.config.get('SPOT_SIZE_WARNING'), 'Relative': True}  # %

        # Analyze opg file

        self.filename = opgfile
        self.reportDate = datetime.fromtimestamp(os.path.getmtime(opgfile))
        self.energies = [240, 210, 180, 160, 140, 110, 80]

        self.xa, self.ya, self.doseArray = opgread(self.filename)
        xb, yb, db, doseCAX = interp2d(self.xa, self.ya, self.doseArray)
        # xo, yo, do, doseCAXo = interp2d(xa, ya, self.doseArray, toOrigin=True)
        self.background = checkBackground(xb, yb, db)
        self.spotQA = checkSpot(xb, yb, db - self.background) # spotQA.append({'XOff': x, 'YOff': y, 'XSigma': xsigma, 'YSigma': ysigma})
        self.profileQA = checkProfile(xb, yb, db) # profileQA.append((lp, rp, fs, flatness, symmetry))
        self.output = checkOutput(xb, yb, db)
        self.energy = checkEnergy(xb, yb, db)


        # Compare
        self.outputPass = check(self.output, self.baseline['Output'], self.outputLevel)
        self.energyPass = check(self.energy, self.baseline['Energy'], self.energyLevel)
        self.spotPositionXPass = check(pd.DataFrame(self.spotQA)['XOff'].values,
                                      pd.DataFrame(self.baseline['SpotQA'])['XOff'].values, self.spotPositionLevel)
        self.spotSizeXPass = check(pd.DataFrame(self.spotQA)['XSigma'].values,
                                  pd.DataFrame(self.baseline['SpotQA'])['XSigma'].values, self.spotSizeLevel)
        self.spotPositionYPass = check(pd.DataFrame(self.spotQA)['YOff'].values,
                                       pd.DataFrame(self.baseline['SpotQA'])['YOff'].values,
                                       self.spotPositionLevel)
        self.spotSizeYPass = check(pd.DataFrame(self.spotQA)['YSigma'].values,
                                   pd.DataFrame(self.baseline['SpotQA'])['YSigma'].values,
                                   self.spotSizeLevel)

        if 'Fail' in self.spotPositionYPass or 'Fail' in self.spotPositionXPass:
            self.spotPositionCheck = 'Fail'
        elif 'Warning' in self.spotPositionYPass or 'Warning' in self.spotPositionXPass:
            self.spotPositionCheck = 'Warning'
        else:
            self.spotPositionCheck = 'Pass'
        if 'Fail' in self.spotSizeYPass or 'Fail' in self.spotSizeXPass:
            self.spotSizeCheck = 'Fail'
        elif 'Warning' in self.spotSizeYPass or 'Warning' in self.spotSizeXPass:
            self.spotSizeCheck = 'Warning'
        else:
            self.spotSizeCheck = 'Pass'

        self.note = r['note']
        self.mapfname = 'test.png'

    @classmethod
    def CreateFromResponse(cls, resp, uploadFolder):

        r={}
        # Mechanical and Safety
        r['room'] = resp.form.get('selectRoom')
        r["therapist"] = resp.form.get('inputTherapist')
        r["doorWarning"] = resp.form.get('checkDoorWarning')
        r["doorInterlock"] = resp.form.get('checkDoorInterlock')
        r["intercom"] = resp.form.get('checkIntercom')
        r["videoMonitor"] = resp.form.get('checkVideoMonitor')
        r["searchButton"] = resp.form.get('checkSearchButton')
        r["radiationMonitor"] = resp.form.get('checkRadiationMonitor')
        r["beamPause"] = resp.form.get('checkBeamPause')
        r["collisionInterlock"] = resp.form.get('checkCollisionInterlock')
        r["beamOnIndicator"] = resp.form.get('checkBeamOnIndicator')
        r["xrayOnIndicator"] = resp.form.get('checkXrayOnIndicator')

        # Image
        r["panelA"] = resp.form.get('checkPanelA')
        r["panelB"] = resp.form.get('checkPanelB')
        r["CBCTA"] = resp.form.get('checkCBCTA')
        r["CBCTB"] = resp.form.get('checkCBCTB')

        # Laser
        r["laserSI"] = resp.form.get('checkLaserSI')
        r["laserRL"] = resp.form.get('checkLaserRL')
        r["laserAP"] = resp.form.get('checkLaserAP')

        opgfile = os.path.join(uploadFolder, resp.files["inputfile"].filename)

        # Note
        r["note"] = resp.form.get('textNote')
        return DailyQARecord(r, opgfile)


    @classmethod
    def CreateFromFile(cls, opgfile, room, therapist='therapist', r=None):

        if r == None:
            r = {}
            # Mechanical and Safety
            r['room'] = room
            r["therapist"] = therapist
            r["doorWarning"] = 'Pass'
            r["doorInterlock"] = 'Pass'
            r["intercom"] = 'Pass'
            r["videoMonitor"] = 'Pass'
            r["searchButton"] = 'Pass'
            r["radiationMonitor"] = 'Pass'
            r["beamPause"] = 'Pass'
            r["collisionInterlock"] = 'Pass'
            r["beamOnIndicator"] = 'Pass'
            r["xrayOnIndicator"] = 'Pass'

            # Image
            r["panelA"] = 'Pass'
            r["panelB"] = 'Pass'
            r["CBCTA"] = 'Pass'
            r["CBCTB"] = 'Pass'

            # Laser
            r["laserSI"] = 'Pass'
            r["laserRL"] = 'Pass'
            r["laserAP"] = 'Pass'

            # Error/Warning Level; because the flask app is not created so no level is set
            r["outputLevel"] = {'Fail': 0.05, 'Warning': 0.03, 'Relative': True}
            r["energyLevel"] = {'Fail': 0.12, 'Warning': 0.06, 'Relative': True}
            r["spotPositionLevel"] = {'Fail': 2.0, 'Warning': 1.5, 'Relative': False}
            r["spotSizeLevel"] = {'Fail': 0.2, 'Warning': 0.1, 'Relative': True}

            # Note
            r["note"] = ''

        return DailyQARecord(r, opgfile)


    def QAResults(self):

        return getResults(self)


    def renderReport(self):
        return getReport(self)


    def writeToDB(self):
        sqlite3.register_adapter(np.ndarray, adapt_array)

        sqlite3.register_converter("array", convert_array)

        spotQAdf = pd.DataFrame(self.spotQA)
        XOfflist = ';'.join([str(i) for i in spotQAdf.XOff])
        YOfflist = ';'.join([str(i) for i in spotQAdf.YOff])
        XSigmaList = ';'.join([str(i) for i in spotQAdf.XSigma])
        YSigmaList = ';'.join([str(i) for i in spotQAdf.YSigma])
        conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__)) + '/DailyQA.db', detect_types=sqlite3.PARSE_DECLTYPES)
        cur = conn.cursor()
        qry = 'insert into DailyQARecord ('
        qry += 'therapist, createDate, room, doorWarning, doorInterlock, intercom, videoMonitor, '
        qry += 'searchButton, radiationMonitor, beamPause, collisionInterlock, beamOnIndicator, '
        qry += 'xrayOnIndicator, safetyCheck, panelA, panelB, '
        qry += 'CBCTA, CBCTB, imageCheck, laserSI, laserRL, laserAP, laserCheck, xa, ya, doseArray, calculated, excluded, '
        qry += 'energies, fieldSizeX, fieldSizeY, leftPenumbra, '
        qry += 'rightPenumbra, upPenumbra, downPenumbra, flatnessX, flatnessY, '
        qry += 'symmetryX, symmetryY, outputPass, energyPass, spotPositionXPass, '
        qry += 'spotPositionYPass, spotPositionCheck, spotSizeXPass, spotSizeYPass, '
        qry += 'spotSizeCheck, background, output, energy, spotXOff, spotYOff, '
        qry += 'spotXSigma, spotYSigma, note) values ('
        qry += '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '
        qry += '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '
        qry += '?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(qry,
                    (self.therapist, self.reportDate, self.room, self.doorWarning, self.doorInterlock, self.intercom,
                     self.videoMonitor, self.searchButton, self.radiationMonitor, self.beamPause, self.collisionInterlock,
                     self.beamOnIndicator, self.xrayOnIndicator, self.safetyCheck,
                     self.panelA, self.panelB, self.CBCTA, self.CBCTB, self.imageCheck, self.laserSI, self.laserRL,
                     self.laserAP, self.laserCheck, self.xa, self.ya, self.doseArray, True, False,
                     ';'.join([str(i) for i in self.energies]), self.profileQA[0][2], self.profileQA[1][2],
                     self.profileQA[0][0], self.profileQA[0][1], self.profileQA[1][1], self.profileQA[1][0],
                     self.profileQA[0][3], self.profileQA[1][3], self.profileQA[0][4], self.profileQA[1][4],
                     self.outputPass, self.energyPass, ';'.join(self.spotPositionXPass), ';'.join(self.spotPositionYPass),
                     self.spotPositionCheck, ';'.join(self.spotSizeXPass), ';'.join(self.spotSizeYPass),
                     self.spotSizeCheck, self.background, self.output, self.energy, XOfflist, YOfflist, XSigmaList, YSigmaList,
                     self.note))
        conn.commit()
        conn.close()


def adapt_array(arr):
    out = io.BytesIO()
    np.save(out, arr)
    out.seek(0)
    return sqlite3.Binary(out.read())


def convert_array(text):
    out = io.BytesIO(text)
    out.seek(0)
    return np.load(out)