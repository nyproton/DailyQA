import os
from flask import Flask, render_template, request, redirect, flash, make_response, url_for
from DailyQARecord import DailyQARecord
from datetime import timedelta
from dateutil import parser
from flask_weasyprint import HTML, render_pdf
import pickle
from matplotlib.figure import Figure
from matplotlib import cm
import matplotlib.pyplot as plt
import matplotlib
import sqlite3
import json
matplotlib.use('Agg')


# from browseDICOM import browseDICOM


ALLOWED_EXTENSIONS = ['opg']
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/uploads/'
DAILYQARESULT_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/dailyQAresults/'
DAILYQA_DATABASE = os.path.dirname(os.path.abspath(__file__)) + '/DailyQA.db'

TEMP_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/tmp/'
DICOM_FOLDER = '\\\\10.11.120.7\\VA_DATA$\\DICOM'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER
app.config['DICOM_FOLDER'] = DICOM_FOLDER
app.config['DAILYQARESULT_FOLDER'] = DAILYQARESULT_FOLDER
app.jinja_env.filters['zip'] = zip


app.config['OUTPUT_WARNING'] = 0.03
app.config['OUTPUT_FAIL'] = 0.05
app.config['ENERGY_WARNING'] = 0.06
app.config['ENERGY_FAIL'] = 0.12
app.config['SPOT_POSITION_WARNING'] = 1.5
app.config['SPOT_POSITION_FAIL'] = 2.0
app.config['SPOT_SIZE_WARNING'] = 0.1
app.config['SPOT_SIZE_FAIL'] = 0.2


@app.route("/")
def index():
    return render_template('index.html')
	

@app.route("/about")
def about():
    return render_template('about.html')
	

@app.route("/dailyQA", methods=['GET', 'POST'])
def dailyQA():
    results = []
    return render_template('dailyQA.html', results=results)


@app.route("/dailyQANew")
def dailyQANew():
    results = []
    return render_template("dailyQANew.html", results=results)


@app.route("/dailyQAResult", methods=['GET', 'POST'])
def dailyQAResult():
    results = []
    if request.method == "POST":
        if 'inputfile' not in request.files:
            flash('No file information')
            return redirect(request.url)
        opgFile = request.files["inputfile"]
        if opgFile.filename == '':
            flash('No file information')
            return redirect(request.url)
        if opgFile and allowed_file(opgFile.filename):
            fname = os.path.join(app.config['UPLOAD_FOLDER'], opgFile.filename)
            if os.path.exists(fname):
                os.remove(fname)
            opgFile.save(fname)

            dailyQARecord=DailyQARecord.CreateFromResponse(request, app.config['UPLOAD_FOLDER'])
            results = dailyQARecord.QAResults()
            dailyQARecord.writeToDB()

            # add a backup to dailyQAresults folder
            fname = dailyQARecord.reportDate.strftime("%m%d%Y_%H%M%S") + '.opg'
            opgFile.save(os.path.join(app.config['DAILYQARESULT_FOLDER'], dailyQARecord.room, fname))

            # save a graph of dailyQA to dosemap folder
            graphfname = os.path.dirname(os.path.abspath(__file__)) + '/static/dosemap/' + 'test1.png'
            if os.path.exists(graphfname):
                os.remove(graphfname)
            f, ax = plt.subplots()
            ax.set_title('Matrixx Results')
            ax.set_aspect('equal')
            ax.pcolormesh(dailyQARecord.xa, dailyQARecord.ya, dailyQARecord.doseArray, cmap=cm.jet)
            f.savefig(os.path.dirname(os.path.abspath(__file__)) + '/static/dosemap/' + 'graph.png')

            picklefname =os.path.join(app.config['TEMP_FOLDER'],'{}_{}.pickle'.format(dailyQARecord.reportDate.strftime("%m%d%y_%H%M%S"), dailyQARecord.room))
            if os.path.exists(picklefname):
                os.remove(picklefname)
            with open(picklefname,'wb') as f:
                pickle.dump(dailyQARecord, f, pickle.HIGHEST_PROTOCOL)

            resp = make_response(render_template("dailyQAResult.html", results=results))
            resp.set_cookie('picklefname', picklefname)
        else:
            resp = make_response(url_for('index'))

    return resp

    
@app.route("/dailyQAReport")
def dailyQAReport():
    # files=os.listdir(app.config['TEMP_FOLDER'])
    # if len(files) > 0:
    #     picklefname = os.path.join(app.config['TEMP_FOLDER'], files[0])
    picklefname = request.cookies.get('picklefname')
    if picklefname is not None:
        if os.path.exists(picklefname):
            with open(picklefname, 'rb') as f:
                dailyQARecord = pickle.load(f)

            os.remove(picklefname)
            html = render_template('dailyReport.html', qa=dailyQARecord.renderReport())
            return render_pdf(HTML(string=html), download_filename='{}_{}.pdf'.format(dailyQARecord.room, dailyQARecord.reportDate))
            # return html
            # resp = make_response(dailyQARecord.GenerateReport()) #io byte
            # resp.headers['Content-Disposition'] = "attachment; filename=%s" % 'test.pdf'
            # resp.mimetype = 'application/pdf'
            # return resp
        else:
            return 'File is not ready, use go back button to go back.'
    else:
        return 'File is not ready, try later.'


@app.route("/dailyQASetup", methods=['GET', 'POST'])
def dailyQASetup():
    if request.method == "POST":
        reqPost = True
        app.config['OUTPUT_WARNING'] = float(request.form.get('OutputWarning')) / 100.0
        app.config['OUTPUT_FAIL'] = float(request.form.get('OutputFail')) / 100.0
        app.config['ENERGY_WARNING'] = float(request.form.get('EnergyWarning')) / 100.0
        app.config['ENERGY_FAIL'] = float(request.form.get('EnergyFail')) / 100.0
        app.config['SPOT_POSITION_WARNING'] = float(request.form.get('SpotPositionWarning'))
        app.config['SPOT_POSITION_FAIL'] = float(request.form.get('SpotPositionFail'))
        app.config['SPOT_SIZE_WARNING'] = float(request.form.get('SpotSizeWarning')) / 100.0
        app.config['SPOT_SIZE_FAIL'] = float(request.form.get('SpotSizeFail')) / 100.0
    else:
        reqPost = False
    return render_template("dailyQASetup.html", config=app.config, reqPost=reqPost)


@app.route("/dailyQAList", methods=['GET', 'POST'])
def dailyQAList():
    if request.method == "POST":
        room = request.form.get('selectRoom')
        startDate = parser.parse(request.form.get('inputStartDate'))
        endDate = parser.parse(request.form.get('inputEndDate'))
        paras = (room, startDate, endDate + timedelta(days=1))
        details = {}
        details["safety"] = 'checkSafety' in request.form
        details["image"] = 'checkImage' in request.form
        details["laser"] = 'checkLaser' in request.form
        details["output"] = 'checkOutput' in request.form
        details["energy"] = 'checkEnergy' in request.form
        details["profile"] = 'checkProfile' in request.form
        details["spotPosition"] = 'checkSpotPosition' in request.form
        details["spotSize"] = 'checkSpotSize' in request.form
        conn = sqlite3.connect(DAILYQA_DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM DailyQARecord WHERE room=? AND createDate BETWEEN ? AND ?", paras)
        rows = cur.fetchall()
        conn.close()
        return render_template("dailyQAList.html", details=details, results=rows, room=room,
                               startDate=startDate.strftime("%m-%d-%Y"), endDate=endDate.strftime("%m-%d-%Y"))
    else:
        details = {}
        details["safety"] = False
        details["image"] = False
        details["laser"] = False
        details["output"] = False
        details["energy"] = False
        details["spotPosition"] = False
        details["spotSize"] = False
        return render_template("dailyQAList.html", results=None, room='', details=details, startDate='MM/DD/YYYY', endDate='MM/DD/YYYY')

@app.route("/dailyQABaseline", methods=['GET', 'POST'])
def dailyQABaseline():
    if request.method == "POST":
        room = request.form.get('selectRoom')
        infile = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'baseline', '{}_baseline.json'.format(room)))
        data = json.load(infile)
        infile.close()
        return render_template("dailyQABaseline.html", room=room, data=data)
    else:
        return render_template("dailyQABaseline.html", room='', data='')

# @app.route("/cropCT")
# def cropCT():
#   results = browseDICOM(app.config['DICOM_FOLDER'])
#   return render_template("cropCT.html", results = results)
#
# @app.route("/danielPage")
# def danielPage():
# 	num = "Hello World!"
# 	return render_template("danielPage.html", results = num)


if __name__ == "__main__":
    app.run(port=80)