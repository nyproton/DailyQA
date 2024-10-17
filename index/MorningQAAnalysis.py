from MatrixxUtil import opgread
from scipy import interpolate, optimize
import numpy as np
import os
import json
import pandas as pd


def interp2d(xgrid, ygrid, opgdata, **kwargs):

    # using mm as unit, -118 to 119 is the ion chamber region for Matrixx PT, space is 1mm
    f = interpolate.interp2d(xgrid, ygrid, opgdata, kind='linear')

    if kwargs.pop('toOrigin', False): # if 'toOrigin=True', use 32x32 from -118.0945 to 118.0945
        xnew = np.arange(-118.0945, 118.1, 7.619)
        ynew = np.arange(-118.0945, 118.1, 7.619)
    else:
        xnew = np.arange(-118, 119, 1)
        ynew = np.arange(-118, 119, 1)
    znew = f(xnew, ynew)
    doseCAX = f(0.0, 0.0)
    return xnew, ynew, znew, doseCAX


def doseByCoords(xcoord, ycoord, xgrid, ygrid, doseArray):
    f = interpolate.interp2d(xgrid, ygrid, doseArray, kind='linear')
    return f(xcoord, ycoord)


def checkBackground(xgrid, ygrid, doseArray):
    # magic number: xgrid: 95.2375 to 118.0945 ygrid: -11.4285 to 11.4285 space is 7.619

    xcoord = np.arange(95.2375, 118.0945 + 0.1, 7.619)
    ycoord = np.arange(-11.4285, 11.4285 + 0.1, 7.619)
    return np.mean(doseByCoords(xcoord, ycoord, xgrid, ygrid, doseArray))


def gaussian(height, center_x, center_y, width_x, width_y):
    """Returns a gaussian function with the given parameters"""
    width_x = float(width_x)
    width_y = float(width_y)
    return lambda x,y: height*np.exp(-(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)


def moments(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution by calculating its
    moments """
    total = data.sum()
    X, Y = np.indices(data.shape)
    x = (X*data).sum()/total
    y = (Y*data).sum()/total
    col = data[:, int(y)]
    width_x = np.sqrt(np.abs((np.arange(col.size)-y)**2*col).sum()/col.sum())
    row = data[int(x), :]
    width_y = np.sqrt(np.abs((np.arange(row.size)-x)**2*row).sum()/row.sum())
    height = data.max()
    return height, x, y, width_x, width_y


def fitgaussian(data):
    """Returns (height, x, y, width_x, width_y)
    the gaussian parameters of a 2D distribution found by a fit"""
    params = moments(data)
    errorfunction = lambda p: np.ravel(gaussian(*p)(*np.indices(data.shape)) - data)
    p, success = optimize.leastsq(errorfunction, params)
    return p


def checkSpot(xgrid, ygrid, doseArray):
    # spot position: for 7 energies: 240, 210, 180, 160, 140, 110, 80 space is 7.619mm
    idxy0 = [[95.2375, 95.2375], [34.2855, 95.2375], [-34.2855, 95.2375], [-95.2375, 95.2375], [-64.7615, -95.2375], [-3.8095, -95.2375], [64.7615, -95.2375]]
    spacing = 7.619
    nd = 2 # using 2 detectors each to check

    spotQA = []
    for i in idxy0:
        xcoord = np.arange(i[0] - nd * spacing, i[0] + nd * spacing + 0.1, 1)
        ycoord = np.arange(i[1] - nd * spacing, i[1] + nd * spacing + 0.1, 1)
        data = doseByCoords(xcoord, ycoord, xgrid, ygrid, doseArray)
        (height, y, x, ysigma, xsigma) = fitgaussian(data)
        x -= spacing * nd
        y -= spacing * nd
        spotQA.append({'XOff': x, 'YOff': y, 'XSigma': xsigma, 'YSigma': ysigma})
    return spotQA


def profileAnalysis(coord, prof):
    cax = prof[len(prof) // 2]
    prof20 = np.where(prof > (cax * 0.2))
    prof50 = np.where(prof > (cax * 0.5))
    l50 = prof50[0][0]
    r50 = prof50[0][-1]
    prof80 = np.where(prof > (cax * 0.8))
    lp = coord[prof80[0][0]] - coord[prof20[0][0]]
    rp = coord[prof20[0][-1]] - coord[prof80[0][-1]]
    fs = coord[r50] - coord[l50]

    w80 = prof[(coord > coord[l50] * 0.8) & (coord < coord[r50] * 0.8)]
    flatness = (w80.max() - w80.min()) / (w80.max() + w80.min()) * 100
    lt_area = sum(w80[:len(w80) // 2])
    rt_area = sum(w80[len(w80) // 2:])
    symmetry = (lt_area - rt_area) / (lt_area + rt_area) * 100

    return lp, rp, fs, flatness, symmetry


def checkProfile(xgrid, ygrid, doseArray):  # return left penumbra, right penumbera, field size, flatness and symmetry
    # magic number: xcoord: -72.3805 to 72.3805, ycoord: -72.3805 to 72.3805, space: 7.619
    xcoord = np.arange(-72.3805, 72.3805 + 0.1, 1)
    ycoord = np.arange(-72.3805, 72.3805 + 0.1, 1)
    xdata = doseByCoords(xcoord, 0, xgrid, ygrid, doseArray)
    ydata = doseByCoords(0, ycoord, xgrid, ygrid, doseArray)
    profileQA = []
    lp, rp, fs, flatness, symmetry = profileAnalysis(xcoord, xdata.ravel())
    profileQA.append((lp, rp, fs, flatness, symmetry))
    lp, rp, fs, flatness, symmetry = profileAnalysis(ycoord, ydata.ravel())
    profileQA.append((lp, rp, fs, flatness, symmetry))

    return profileQA


def checkOutput(xgrid, ygrid, doseArray):
    spacing = 7.619
    nd = 1.0  # using 0.5 detectors each to check
    xcoord = np.arange(0.0 - nd * spacing, 0.0 + nd * spacing + 0.1, 1)
    ycoord = np.arange(0.0 - nd * spacing, 0.0 + nd * spacing + 0.1, 1)
    return np.mean(doseByCoords(xcoord, ycoord, xgrid, ygrid, doseArray))

def checkEnergy(xgrid, ygrid, doseArray):
    # magic number: xcord: -110.4755 to -95.2375, ycord: -11.4285 to 11.4285

    xcoord = np.arange(-110.4755, -95.2375 + 0.1, 7.619)
    ycoord = np.arange(-11.4285, 11.4285 + 0.1, 7.619)
    return np.max(doseByCoords(xcoord, ycoord, xgrid, ygrid, doseArray))


def compare(meas, baseline, isrelative):
    meas = np.asanyarray(meas) * 1.0
    baseline = np.asanyarray(baseline) * 1.0
    if isrelative:
        return (meas - baseline) / baseline
    else:
        return (meas - baseline)


def check(meas, baseline, level):
    diff = compare(meas, baseline, level['Relative'])
    if isinstance(diff, np.ndarray):
        result = []
        for d in diff:
            if (abs(d) >= level['Fail']).any():
                result.append('Fail')
            elif (abs(d) >= level['Warning']).any():
                result.append('Warning')
            else:
                result.append('Pass')
        return result
    else:
        if abs(diff) >= level['Fail']:
            return 'Fail'
        elif abs(diff) >= level['Warning']:
            return 'Warning'
        else:
            return 'Pass'

def saveBaseline(output, energy, spotQA, profileQA, room):
    data = {}
    data['Room'] = room
    data['Output'] = output
    data['Energy'] = energy
    data['SpotQA'] = spotQA
    data['ProfileQA'] = profileQA
    with open(os.path.join('baseline', '{}_baseline.json'.format(room)), 'w') as outfile:
        json.dump(data, outfile)


def readBaseline(room):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'baseline', '{}_baseline.json'.format(room))) as infile:
        data = json.load(infile)
        return data


def createBaseline(filename, room):
    xa, ya, doseArray = opgread(filename)
    xb, yb, db, doseCAX = interp2d(xa, ya, doseArray)
    # xo, yo, do, doseCAXo = interp2d(xa, ya, doseArray, toOrigin=True)
    background = checkBackground(xb, yb, db)
    spotQA = checkSpot(xb, yb, db - background)
    profileQA = checkProfile(xb, yb, db - background)
    output = checkOutput(xb, yb, db - background)
    energy = checkEnergy(xb, yb, db - background)
    saveBaseline(output, energy, spotQA, profileQA, room)

def createBaselineFromFiles(pa, flist, room):
    # baselines = []
    output_sum = 0
    energy_sum = 0
    spotQAs = []
    profileQA = [[0.0] * 5, [0.0] * 5]

    for i in range(7):
        spotQA = {}
        spotQA['XOff'] = 0
        spotQA['YOff'] = 0
        spotQA['XSigma'] = 0
        spotQA['YSigma'] = 0
        spotQAs.append(spotQA)

    for f in flist:
        xa, ya, doseArray = opgread(os.path.join(pa, f))
        xb, yb, db, doseCAX = interp2d(xa, ya, doseArray)
        background = checkBackground(xb, yb, db)
        ss = checkSpot(xb, yb, db - background)
        for s, sp in zip(ss,spotQAs):
            sp['XOff'] += s['XOff']
            sp['YOff'] += s['YOff']
            sp['XSigma'] += s['XSigma']
            sp['YSigma'] += s['YSigma']
        pQA = checkProfile(xb, yb, db - background)
        for i in range(5):
            profileQA[0][i] += pQA[0][i]
            profileQA[1][i] += pQA[1][i]
        output_sum += checkOutput(xb, yb, db - background)
        energy_sum += checkEnergy(xb, yb, db - background)
    n = len(flist)
    output = output_sum / n
    energy = energy_sum / n
    for s in spotQAs:
        s['XOff'] = s['XOff'] / n
        s['YOff'] = s['YOff'] / n
        s['XSigma'] = s['XSigma'] / n
        s['YSigma'] = s['YSigma'] / n
    for i in range(5):
        profileQA[0][i] = profileQA[0][i] / n
        profileQA[1][i] = profileQA[1][i] / n
    print(output, energy)
    print(spotQAs)
    print(profileQA)
    saveBaseline(output, energy, spotQAs, profileQA, room)

if __name__ == '__main__':

######################## Create base line here ############################
    # # filename = r'uploads/TR3 DailyQA baseline 07012019.opg'
    # filename = r'C:\PythonProjects\QATools\index\uploads\TR2 8-22-19.opg'
    # room = 'TR2'
    # createBaseline(filename, room)

######################### Compare with baseline ##############################
    # filename = r'uploads/TR3 DailyQA baseline 07012019.opg'
    # xa, ya, doseArray = opgread(filename)
    # xb, yb, db, doseCAX = interp2d(xa, ya, doseArray)
    # xo, yo, do, doseCAXo = interp2d(xa, ya, doseArray, toOrigin=True)
    # background = checkBackground(xb, yb, db)
    # spotQA = checkSpot(xb, yb, db - background)
    # profileQA = checkProfile(xb, yb, db - background)
    # output = checkOutput(xb, yb, db - background)
    # energy = checkEnergy(xb, yb, db - background)
    # #
    # baseline = readBaseline('TR2')
    #
    # # outputLevel = {'Fail': 0.05, 'Warning': 0.03, 'Relative': True}
    # # outputPass = check(output, baseline['Output'], outputLevel)
    # spotPositionLevel = {'Fail': 2.0, 'Warning': 1.0, 'Relative': False}
    # spotPositionPass = check(pd.DataFrame(spotQA)[['XOff', 'YOff']].values, pd.DataFrame(baseline['SpotQA'])[['XOff', 'YOff']].values, spotPositionLevel)
    # print(spotPositionPass)

    pa = r"C:\PythonProjects\QATools\index\TR1"
    flist = os.listdir(pa)
    room = "TR1"
    createBaselineFromFiles(pa, flist, room)

