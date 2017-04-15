# --coding:utf-8--

import os
import os.path
import shapefile
import struct
import datetime
import decimal
import itertools

# rootdir = "/Users/lishiguang/Documents/data/heilongjiang/index"
rootdir = "H:\\1\\sw2geo\\heilongjiang"

def dbfreader(f):
    """Returns an iterator over records in a Xbase DBF file.

    The first row returned contains the field names.
    The second row contains field specs: (type, size, decimal places).
    Subsequent rows contain the data records.
    If a record is marked as deleted, it is skipped.

    File should be opened for binary reads.

    """
    # See DBF format spec at:
    #     http://www.pgts.com.au/download/public/xbase.htm#DBF_STRUCT

    numrec, lenheader = struct.unpack('<xxxxLH22x', f.read(32))
    numfields = (lenheader - 33) // 32

    fields = []
    for fieldno in xrange(numfields):
        name, typ, size, deci = struct.unpack('<11sc4xBB14x', f.read(32))
        name = name.replace('\0', '')  # eliminate NULs from string
        fields.append((name, typ, size, deci))
    yield [field[0] for field in fields]
    yield [tuple(field[1:]) for field in fields]

    terminator = f.read(1)
    assert terminator == '\r'

    fields.insert(0, ('DeletionFlag', 'C', 1, 0))
    fmt = ''.join(['%ds' % fieldinfo[2] for fieldinfo in fields])
    fmtsiz = struct.calcsize(fmt)
    for i in xrange(numrec):
        record = struct.unpack(fmt, f.read(fmtsiz))
        if record[0] != ' ':
            continue  # deleted record
        result = []
        for (name, typ, size, deci), value in itertools.izip(fields, record):
            if name == 'DeletionFlag':
                continue
            if typ == "N":
                value = value.replace('\0', '').lstrip()
                if value == '':
                    value = 0
                elif deci:
                    value = decimal.Decimal(value)
                else:
                    value = int(value)
            elif typ == 'D':
                y, m, d = int(value[:4]), int(value[4:6]), int(value[6:8])
                value = datetime.date(y, m, d)
            elif typ == 'L':
                value = (value in 'YyTt' and 'T') or (value in 'NnFf' and 'F') or '?'
            elif typ == 'F':
                value = float(value)
            result.append(value)
        yield result

poiPath = rootdir + os.path.sep + "index" + os.path.sep + "POIheilongjiang.shp"
poi = shapefile.Reader(poiPath)
records = poi.records()
poiId2poiInfo = {}      #POIheilongjiang.shp中POI_ID对应的坐标对
featid2name = {}        #PNameheilongjiang.dbf中(featid,language)对应的中文名和英文名，"1"中文，"3"拼音
minx = 180.0
miny = 90.0
maxx = 0.0
maxy = 0.0

for record in records:
    poiId = record[7].strip()
    x = record[5].strip()
    y = record[6].strip()
    poiId2poiInfo[poiId] = (record[5], record[6])

pnamePath = rootdir + os.path.sep + "other" + os.path.sep + "PNameheilongjiang.dbf"
with open(pnamePath, 'rb') as fPName:
    db = list(dbfreader(fPName))
    i = 0
    for record in db:
        if i<2:
            i+=1
            continue
        featid = record[0].strip()
        language = record[8].strip()
        name = record[2].strip().decode('gbk').encode('utf8')
        featid2name[(featid, language)] = name


with open("heilongjiang.osm", "w") as fp:
    fp.write('''<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="CGImap 0.6.0 (17107 thorn-02.openstreetmap.org)" copyright="OpenStreetMap and contributors" attribution="http://www.openstreetmap.org/copyright" license="http://opendatacommons.org/licenses/odbl/1-0/">''')
    fp.write("\n")
    id = 0
    for poiId in poiId2poiInfo.keys():
        id += 1
        x = poiId2poiInfo[poiId][0]
        y = poiId2poiInfo[poiId][1]
        if float(x)<minx:
            minx = float(x)
        if float(x)>maxx:
            maxx = float(x)
        if float(y) < miny:
            miny = float(y)
        if float(y) > maxy:
            maxy = float(y)
        chnName = featid2name[(poiId,"1")]
        pinyin = featid2name[(poiId,"3")]
        fp.write("  <node id=\"%d\" lat=\"%s\" lon=\"%s\" > \n      <tag k=\"name\" v=\"%s\"/>      \n  </node>\n" % (id, x, y, chnName))
    fp.write(" <bounds minlat=\"%s\" minlon=\"%s\" maxlat=\"%s\" maxlon=\"%s\"/>\n" % (str(miny), str(minx), str(maxy), str(maxx)) )
    fp.write('''</osm>''')


#
# with open("town_point.txt", "w") as fp_w:
#     fp_w.write("id	name	adcode	x	y\n")
#     i=1
#     for town in town_datas:
#         fp_w.write( str(i)+"\t"+featid2name[town[3]]+"\t"+town[0]+"\t"+town[1]+"\t"+town[2]+"\n" )
#         i += 1

