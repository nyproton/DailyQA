import os
import subprocess
import pydicom
import pandas


def browseDICOM(dicom_folder):
    netdomain = 'nyproton.com'
    netuser = 'user'
    netpass = 'pass'
    drive = '//10.11.120.7/va_data$/DICOM'
    cmd = r'net use {} /del'.format(drive)
    subprocess.call(cmd, shell=True)
    cmd = 'net use {}  {} /user:{}\\{} {}'.format(drive, dicom_folder, netdomain, netuser, netpass)
    subprocess.call(cmd, shell=True)
    indexfile = 'no_delete.idx'
    df = pandas.read_csv(os.path.join(drive, indexfile), index_col='fname', header=0, names=['fname', 'cdate', 'pname', 'modality'])

    pts = []
    for root, dirs, files in os.walk(drive):
        for f in files:
            if '.dcm' in f:
                fname = os.path.join(root, f)
                found = True
                try:
                    rec = df.loc[fname]
                except KeyError:
                    found = False
                if found:
                    pts.append(rec['pname'])
                else:
                    with pydicom.dcmread(fname) as ds:
                        pts.append(str(ds.PatientName))
    results = {i: pts.count(i) for i in pts}
    return results
