import os
from struct import unpack

from pylab import *

import numpy as np
import matplotlib.cm as cm

resolution = 1201  # 1201, 3601
srtm_format = 3  # 3, 1


class srtmParser(object):
    def parseFile(self, filename):
        fi = open(filename, "rb")
        contents = fi.read()
        fi.close()
        self.data = unpack(">%sH" % memory, contents)

    def writeCSV(self, filename):
        if self.z:
            fo = open(filename, "w")
            for row in range(0, resolution):
                offset = row * resolution
                thisrow = self.z[offset:offset + resolution]
                rowdump = ",".join([str(z) for z in thisrow])
                fo.write("%s\n" % rowdump)
            fo.close()
        else:
            return None

if __name__ == '__main__':
    srtmParser = srtmParser()
    memory = resolution * resolution
    hgt_folder = "hgt/srtm%s" % srtm_format
    img_folder = "img/srtm%s" % srtm_format
    files = os.listdir(hgt_folder)

    for filename in files:
        srtmParser.parseFile('%s/%s' % (hgt_folder, filename))
        outfile = zeros((resolution, resolution))

        for r in range(0, resolution):
            for c in range(0, resolution):
                va = f.data[(resolution * r) + c]
                if (va == 65535 or va < 0 or va > 2000):
                    va = 0.0
                outfile[r][c] = float(va)
        # logarithm color scale
        color_scale = np.log1p(outfile)
        imshow(color_scale, interpolation='bilinear', cmap=cm.gray, alpha=1.0)
        savefig('%s/%s.png' % (img_folder, filename))
