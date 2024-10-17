import numpy as np


def opgread(filename):
    with open(filename) as f:
        fstream = f.read().splitlines()

    fmeta = {}
    for fline in fstream:
        if ':' in fline:
            s = fline.split(':')
            fmeta[s[0].strip()] = s[1].strip()
        if '<asciibody>' in fline:
            line = fstream.index(fline)

    # if fmeta['File Version'] != '3':
    #     raise ValueError('Wrong version, should be version 3!')

    if fmeta['Separator'] == '[Tab]' or fmeta['Separator'] == '[TAB]':
        seperator = '\t'
    elif fmeta['Separator'] == '","':
        seperator = ','
    else:
        raise ValueError('Separator not recognize: {}'.format(fmeta['Separator']))
    if fmeta['Data Unit'] == 'mGy':
        convert2cGy = 0.1
    elif fmeta['Data Unit'] == 'cGy':
        convert2cGy = 1.0
    elif fmeta['Data Unit'] == 'cnt': # This needs to be verified!
        convert2cGy = 0.01

    if fmeta['Length Unit'] == 'cm':
        convert2mm = 10.0
    elif fmeta['Length Unit'] == 'mm':
        convert2mm = 1.0

    ncol = int(fmeta['No. of Columns'])
    nrow = int(fmeta['No. of Rows'])
    xgrid = []
    ygrid = []
    opgdata = np.zeros((nrow, ncol))

    line += + 3
    x = fstream[line].split(seperator)
    if x[0].strip() == 'X[{}]'.format(fmeta['Length Unit']):
        xgrid = [float(i) for i in x[1:-1]]
    else:
        raise ValueError('Read <asciibody> section wrong! Line No. {}'.format(line))

    line += 1
    if fstream[line].strip() != 'Y[{}]'.format(fmeta['Length Unit']):
        raise ValueError('Read <asciibody> section wrong! Line No. {}'.format(line))

    line += 1
    row = 0
    while fstream[line] != '</asciibody>':
        y = fstream[line].split(seperator)
        ygrid.append(float(y[0]))
        opgdata[row, :] = [float(i) for i in y[1:-1]]
        line += 1
        row += 1

    return np.asarray(xgrid) * convert2mm, np.asarray(ygrid) * convert2mm, opgdata * float(fmeta['Data Factor']) * convert2cGy

if __name__ == '__main__':
    xgrid, ygrid, opgdata = opgread(r"P:\_NYPC Physicis\Patient QA plan\Integral 18_06_2019 13_56_36.53.opg")
    print(xgrid.shape, ygrid.shape, opgdata)
