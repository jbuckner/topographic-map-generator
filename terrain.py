from pylab import *

import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt

from srtm import SRTMDownloader

resolution = 999  # 1201, 3601
pixels = resolution * resolution
divisor = resolution + 1.0
srtm_format = 3  # 3, 1
width = 20
height = 20


def update_status(percent):
    sys.stdout.write("\r%3d%%" % percent)
    sys.stdout.flush()

if __name__ == '__main__':
    fig = plt.figure(frameon=False)
    fig.set_size_inches(width, height)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)

    downloader = SRTMDownloader(
        directory="/srtm/version2_1/SRTM%s/" % srtm_format,
        cachedir="cache/srtm%s" % srtm_format)
    downloader.loadFileList()

    for lat in range(36, 39):
        for lng in range(-123, -120):
            tile = downloader.getTile(lat, lng)
            outfile = zeros((resolution, resolution))

            print tile.lat, tile.lon

            c = 0
            for lat_i in range(0, resolution):
                for lng_i in range(0, resolution):
                    lat_point = lat + (lat_i / divisor)
                    lng_point = lng + (lng_i / divisor)
                    alt = tile.getAltitudeFromLatLon(lat_point, lng_point)
                    if alt:
                        outfile[lat_i][lng_i] = float(alt)
                    c = c + 1.0
                    if (c % 1000) == 0:
                        percent_complete = (c / pixels) * 100.0
                        update_status(percent_complete)
            # logarithm color scale
            color_scale = np.log1p(outfile)
            ax.imshow(color_scale, aspect='normal',
                      interpolation='bilinear', cmap=cm.gray, alpha=1.0)
            fig.savefig('images/%sx%s.png' % (lat, lng))
