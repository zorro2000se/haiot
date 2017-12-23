import gpsd
import urllib2
import ssl
import time
from main.admin import models

initialised = False


class State:
    context = ssl._create_unverified_context()
    url_timeout = 5
    device_name = "skoda"
    UPLOAD_SERVER_URL = "https://www.dancristian.ro/nextcloud/index.php/apps/phonetrack/log/gpslogger/" \
                        "643fee139ee4efd90437176e88298a94/{}?lat=<lat>&lon=<lon>&sat=<sat>&alt=<alt>&acc=<acc>&" \
                        "timestamp=<time>&bat=<bat>".format(device_name)
    last = None
    url_buffer = []
    # timestamp with moves that helps reducing gps report frequency
    last_vibrate = None
    last_move_inside = None
    last_move_outside = None


# https://github.com/MartijnBraam/gpsd-py3/blob/master/DOCS.md
def _read_gps():
    r = gpsd.get_current()
    if r.mode < 2:
        print "No gps fix, sats={} valid={}".format(r.sats, r.sats_valid)
    else:
        if r.mode == 2:
            alt = -9999
        else:
            alt = r.alt
        # use battery fields to report horizontal speed
        url = State.UPLOAD_SERVER_URL.replace("<lat>", str(r.lat)).replace("<lon>", str(r.lon)).replace(
            "<alt>", str(alt)).replace("<sat>", str(r.sats_valid)).replace(
            "<acc>", str(r.position_precision()[0])).replace("<bat>", str(r.hspeed)).replace("<time>", str(time.time()))
        State.url_buffer.insert(1, url)
        d = models.Device
        dev = d().query_filter_first(d.name == State.device_name)
        if dev is not None:
            p = models.Position
            pos = p().query_filter_first(p.device_id == dev.id)
            if pos is not None:
                pos.latitude = r.lat
                pos.longitude = r.lon
                pos.hprecision = r.position_precision()[0]
                pos.vprecision = r.position_precision()[1]
                pos.hspeed = r.hspeed
                pos.vspeed = r.vspeed
                pos.satellite = r.sats
                pos.satellite_valid = r.sats_valid


def _upload_buffer():
    for url in list(State.url_buffer):
        try:
            #f = urllib.urlopen(url)
            # https://stackoverflow.com/questions/27835619/urllib-and-ssl-certificate-verify-failed-error
            f = urllib2.urlopen(url, timeout=State.url_timeout, context=State.context)
            resp = f.read()
            if resp == "null":
                State.url_buffer.remove(url)
            else:
                print "Unexpected response {}".format(resp)
        except Exception, ex:
            print ex
            State.url_buffer.append(url)
            print "Buffer has {} elements".format(len(State.url_buffer))


def init():
    global initialised
    try:
        gpsd.connect()
        initialised = True
    except Exception, ex:
        print ex


def thread_run():
    if initialised:
        _read_gps()
    else:
        init()
    _upload_buffer()


if __name__ == "__main__":
    init()
    while True:
        thread_run()
        time.sleep(10)