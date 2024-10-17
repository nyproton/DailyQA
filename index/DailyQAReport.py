
def passtoResult(passResult, itemName, measurement, baseline, unit):
    if passResult == 'Fail':
        return '<small><span class="text-danger">FAIL: Baseline is {1:5.2f}{0}. {2} Measurement is {3:5.2f}{0}</span></small>'.format(
            unit, baseline, itemName, measurement)
    elif passResult == 'Warning':
        return '<small><span class="text-warning">Warning: Baseline is {1:5.2f}{0}. {2} Measurement is {3:5.2f}{0}</span></small>'.format(
            unit, baseline, itemName, measurement)
    elif passResult == 'Pass':
        return '<small><span class="text-success">PASS: Baseline is {1:5.2f}{0}. {2} Measurement is {3:5.2f}{0}</span></small>'.format(
            unit, baseline, itemName, measurement)
    return 'Something Wrong...'

def passtoResult2(passResult, itemName, measurement, unit):
    if passResult == 'Fail':
        return '<small><span class="text-danger">FAIL: {1} Measurement is {2:5.2f}{0}</span></small>'.format(unit, itemName, measurement)
    elif passResult == 'Warning':
        return '<small><span class="text-warning">Warning: {1} Measurement is {2:5.2f}{0}</span></small>'.format(unit, itemName, measurement)
    elif passResult == 'Pass':
        return '<small><span class="text-success">PASS: {1} Measurement is {2:5.2f}{0}</span></small>'.format(unit, itemName, measurement)
    return 'Something Wrong...'

def getResults(r):  # r as DailyQARecord
    results = []  # results[-1]='pass' or 'fail' or 'warning'
    failflag = 0
    warningflag = 0

    results.append('<h3>Results Analysis of Matrixx Measurement:</h3>')

    # check Background
    if r.background > 1.0:
        results.append('Warning: Make sure background is checked.')
        warningflag = 1

    # check output
    results.append(passtoResult(r.outputPass, 'Output', r.output, r.baseline['Output'], 'cGy'))

    # check energy
    results.append(passtoResult(r.energyPass, 'Energy', r.energy, r.baseline['Energy'], 'cGy'))

    # check profile??

    # check spot
    for i in range(7):
        results.append(passtoResult2(r.spotPositionXPass[i], 'Spot {} X Position'.format(i), r.spotQA[i]['XOff'] - r.baseline['SpotQA'][i]['XOff'], 'mm'))
        results.append(passtoResult2(r.spotPositionYPass[i], 'Spot {} Y Position'.format(i), r.spotQA[i]['YOff'] - r.baseline['SpotQA'][i]['YOff'], 'mm'))
        results.append(passtoResult(r.spotSizeXPass[i], 'Spot {} X Size'.format(i), r.spotQA[i]['XSigma'],
                                   r.baseline['SpotQA'][i]['XSigma'], 'mm'))
        results.append(passtoResult(r.spotSizeYPass[i], 'Spot {} Y Size'.format(i), r.spotQA[i]['YSigma'],
                                   r.baseline['SpotQA'][i]['YSigma'], 'mm'))
    if warningflag == 1:
        results.append('Warning')
    elif failflag == 1:
        results.append('Fail')
    else:
        results.append('pass')

    return results


def ConditionalColor(result):
    if result == "Pass" or result == "Functional":
        return '<span style="color:green">{}</span>'.format(result)
    if result == "Fail" or result == "Not Functional":
        return '<strong><span style="color:red">{}</span></strong>'.format(result)
    if result == "Warning":
        return '<strong><span style="color:yellow">{}</span></strong>'.format(result)
    return result


def getReport(qa):
    qa1 = qa
    qa1.reportDate = qa.reportDate.strftime("%m/%d/%Y_%H:%M:%S")
    qa1.doorWarning = ConditionalColor('Functional') if qa.doorWarning == 'Pass' else 'Not Functional'
    qa1.doorInterlock = ConditionalColor('Functional') if qa.doorInterlock == 'Pass' else 'Not Functional'
    qa1.intercom = ConditionalColor('Functional') if qa.intercom == 'Pass' else 'Not Functional'
    qa1.videoMonitor = ConditionalColor('Functional') if qa.videoMonitor == 'Pass' else 'Not Functional'
    qa1.searchButton = ConditionalColor('Functional') if qa.searchButton == 'Pass' else 'Not Functional'
    qa1.radiationMonitor = ConditionalColor('Functional') if qa.radiationMonitor == 'Pass' else 'Not Functional'
    qa1.beamPause = ConditionalColor('Functional') if qa.beamPause == 'Pass' else 'Not Functional'
    qa1.collisionInterlock = ConditionalColor('Functional') if qa.collisionInterlock == 'Pass' else 'Not Functional'
    qa1.beamOnIndicator = ConditionalColor('Functional') if qa.beamOnIndicator == 'Pass' else 'Not Functional'
    qa1.xrayOnIndicator = ConditionalColor('Functional') if qa.xrayOnIndicator == 'Pass' else 'Not Functional'
    qa1.panelA = ConditionalColor(qa.panelA)
    qa1.panelB = ConditionalColor(qa.panelB)
    qa1.CBCTA = ConditionalColor(qa.CBCTA)
    qa1.CBCTB = ConditionalColor(qa.CBCTB)
    qa1.laserSI = ConditionalColor(qa.laserSI)
    qa1.laserRL = ConditionalColor(qa.laserRL)
    qa1.laserAP = ConditionalColor(qa.laserAP)
    qa1.outputPass = ConditionalColor(qa.outputPass)
    qa1.energyPass = ConditionalColor(qa.energyPass)
    for i in range(len(qa.spotPositionXPass)):
        qa1.spotPositionXPass[i] = ConditionalColor(qa.spotPositionXPass[i])
    for i in range(len(qa.spotPositionYPass)):
        qa1.spotPositionYPass[i] = ConditionalColor(qa.spotPositionYPass[i])
    for i in range(len(qa.spotSizeXPass)):
        qa1.spotSizeXPass[i] = ConditionalColor(qa.spotSizeXPass[i])
    for i in range(len(qa.spotSizeYPass)):
        qa1.spotSizeYPass[i] = ConditionalColor(qa.spotSizeYPass[i])
    qa1.mapfname = qa.mapfname
    return qa1


if __name__ == '__main__':
    pass