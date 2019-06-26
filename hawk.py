import click

import subprocess
import math
import json
import sys
import os
import re
from collections import defaultdict

# Constants
OPEN_LOG_PATH = "/home/pi/Documents/army/shd/scripts/hawk/open_log.py"
#

class Line:

    types = defaultdict(list)
    timestamps = defaultdict(list)
    objs = []

    def __init__(self, dic):
        self.raw_dic = dic

        self.metadata = dic['meta']
        self.data     = dic['data']
        self.type = self.metadata['type']
        self.timestamp = self.metadata['timestamp']

        Line.types[self.type].append(self)
        Line.timestamps[self.timestamp].append(self)
        Line.objs.append(self)

    @classmethod
    def get_nearest(cls, timestamp, type_name):
        assert type_name in Line.types, "Required type doesn't exist"

        sorted_ts = sorted(Line.timestamps.keys())
        min_dif = abs(timestamp - sorted_ts[0])
        prev_dif = min_dif
        for ts in sorted_ts:
            data = Line.timestamps[ts]
            line = None
            for elem in data:
                if elem.type == type_name:
                    line = elem
                    break

            if not line:
                continue
            dif = abs(timestamp-ts)
            if dif < min_dif:
                min_dif = dif
            if dif > prev_dif:
                return line
            prev_dif = dif


    def __repr__(self):
        s = "{} - data keys: {}, (at {})".format(self.type,
                                                 ', '.join(list(self.data.keys())),
                                                self.timestamp)
        return s

class PixhawkLog:

    def __init__(self, filename):

        self.filename = filename
        self.raw_content  = self.open_log(filename)
        self.lines = [Line(line) for line in
                      self.log_output_to_json(self.raw_content)]

    def get_types(self):
        return self.lines[0].types.keys()

    def log_output_to_json(self,out):
        out = out.replace('\n',',')
        out = '[' + out[:-1] + ']'
        out = json.loads(out)
        return out

    def open_log(self, file):
        interpreter_name = sys.executable
        b_out = subprocess.check_output([interpreter_name, OPEN_LOG_PATH, '--format','json',file])
        out = b_out.decode('utf-8')
        return out

    def get_time_attr(self, timestamp, attr_type):

        sorted_ts = sorted(Line.timestamps.keys())

        assert len(Line.timestamps), "No timestamp recorded"
        assert timestamp >= sorted_ts[0], "Required timestamp is below lowest record (required: {}, lowest: {})".format(timestamp, sorted_ts[0])
        assert timestamp < sorted_ts[-1], "Required timestamp is above highest record (required: {}, highest: {})".format(timestamp, sorted_ts[-1])

        line = Line.get_nearest(timestamp, attr_type)
        return line

class ProtrackLog:

    def __init__(self, filename):

        # Config
        self.timestamp_format = '{:10.4f}'
        self.altitude_format  = '{:.2f}'
        self.heading_format   = '{:.2f}'
        self.pitch_format     = '{:.2f}'
        self.roll_format      = '{:.2f}'
        self.coord_format     = '{:.6f}'

        self.line_format = '\t'.join(['time', 'altitude', 'bearing', 'depression',
                            'uaveast', 'heading', 'uavnorth', 'pitch', 'roll',
                            'horizfov', 'vertfov', 'sensortype', 'dayornight',
                            'azimerr', 'eleverr', 'orleft', 'orright', 'ortop',
                            'orbottom'])

        self.filename = filename

        self.attributes_dic = {
            'time':         self.get_time,
            'altitude':     self.get_altitude,
            'bearing':      self.get_bearing,
            'depression':   self.get_depression,
            'uaveast':      self.get_uaveast,
            'heading':      self.get_heading,
            'uavnorth':     self.get_uavnorth,
            'pitch':        self.get_pitch,
            'roll':         self.get_roll,
            'horizfov':     self.get_horizfov,
            'vertfov':      self.get_vertfov,
            'sensortype':   self.get_sensortype,
            'dayornight':   self.get_dayornight,
            'azimerr':      self.get_azimerr,
            'eleverr':      self.get_eleverr,
            'orleft':       self.get_orleft,
            'orright':      self.get_orright,
            'ortop':        self.get_ortop,
            'orbottom':     self.get_orbottom,
        }

    def get_time(self, ph_log, timestamp):
        timestamp = self.timestamp_format.format(timestamp)
        timestamp = float(timestamp)
        return timestamp

    def get_altitude(self, ph_log, timestamp):
        gps = ph_log.get_time_attr(timestamp, 'GPS')
        alt = gps.data['Alt']

        alt = float(self.altitude_format.format(alt))
        return alt

    def get_bearing(self, ph_log, timestamp):
        return 0

    def get_depression(self, ph_log, timestamp):
        return 0 

    def get_uaveast(self, ph_log, timestamp):
        gps = ph_log.get_time_attr(timestamp, 'GPS')
        lon = gps.data['Lng']
        lon = float(self.coord_format.format(lon))
        return lon

    def get_heading(self, ph_log, timestamp):
        mag = ph_log.get_time_attr(timestamp, 'MAG')
        magx, magy = mag.data['MagX'], mag.data['MagY']
        ofsx, ofsy = mag.data['OfsX'], mag.data['OfsY']
        x = magx - ofsx
        y = magy - ofsy

        azimuth = 90 - math.atan2(y,x)*180/math.pi

        azimuth = float(self.heading_format.format(azimuth))
        return azimuth

    def get_uavnorth(self, ph_log, timestamp):
        gps = ph_log.get_time_attr(timestamp, 'GPS')
        lat = gps.data['Lat']
        lat = float(self.coord_format.format(lat))
        return lat

    def get_pitch(self, ph_log, timestamp):
        att   = ph_log.get_time_attr(timestamp, 'ATT')
        pitch = att.data['Pitch']

        pitch = float(self.pitch_format.format(pitch))
        return pitch

    def get_roll(self, ph_log, timestamp):
        att   = ph_log.get_time_attr(timestamp, 'ATT')
        roll  = att.data['Roll']
        roll = float(self.roll_format.format(roll))
        return roll

    def get_horizfov(self, ph_log, timestamp): # Operture
        return 106

    def get_vertfov(self, ph_log, timestamp): # Vertical operture
        return 106*3/4

    def get_sensortype(self, ph_log, timestamp):
        return 0

    def get_dayornight(self, ph_log, timestamp):
        return 1

    def get_azimerr(self, ph_log, timestamp):
        return 0

    def get_eleverr(self, ph_log, timestamp):
        return 0

    def get_orleft(self, ph_log, timestamp):
        return 0

    def get_orright(self, ph_log, timestamp):
        return 0

    def get_ortop(self, ph_log, timestamp):
        return 0

    def get_orbottom(self, ph_log, timestamp):
        return 0

    def build_line(self, ph_log, timestamp):

        attrs = {key:f(ph_log, timestamp) for key,f in self.attributes_dic.items()}
        line = '\t'.join([str(att) for att in attrs.values()])
        line += "\n"
        return line

    def get_timestamp_of_frame(self, start_ts, frame_ix, fps):
        return start_ts + frame_ix/fps

    def build_log(self, ph_log, start_ts, frames_n, fps, crop_firstframe_ix):
        outputfile = self.filename

        first_line = self.line_format+'\n'
        second_line = "[sec]\t[feet]\t[deg]\t[deg]\t[meter]\t[deg]\t[meter]\t[deg]\t[deg]\t[deg]\t[deg]\t[int]\t[int]\t[pixel]\t[pixel]\t[pixel]\t[pixel]\n"

        open(outputfile, 'a').write(first_line+second_line)

        ts = self.get_timestamp_of_frame(start_ts, crop_firstframe_ix, fps)
        for frame_ix in range(frames_n):
            line = self.build_line(ph_log, ts)
            open(outputfile, 'a').write(line)
            ts += 1/fps

def get_frame_timestamp(frame_n, fps, start_time):
    return start_time + frame_n/fps

@click.command()
@click.option('--pixhawk_log', help="Path to the pixhawk log", type=str)
@click.option('--output', help="Path to the output file", type=str)
@click.option('--start_ts', help="Timestamp of the first frame in epoch format (10 cyphers+float)", type=float)
@click.option('--frames_nb', help="Number of frames to log", type=int)
@click.option('--fps', help="Fps rate of the video", type=float)
@click.option('--crop_firstframe_ix', help="index of the first frame of the cropped video", type=float)
def main(pixhawk_log, output, start_ts, frames_nb, fps, crop_firstframe_ix):
    """
    Translate a log from pixhawk flight controller to .TLM file (protrack
    format)
    Example of usage: python3 hawk.py --pixhawk_log pixhawk_log_example_2.bin --output .tlm --frames_nb 2 --fps 30 --crop_firstframe_ix 80 --start_ts  1561103385.8849998
    """
    open(output,'w').close()
    in_log = PixhawkLog(pixhawk_log)
    out_log = ProtrackLog(output)
    out_log.build_log(in_log, start_ts, frames_nb, fps, crop_firstframe_ix)

if __name__ == "__main__":
#    main('./pixhawk_log_example_2.bin', 'translated.tlm',  1561103385.79, 80,
#         15, 20)
    main()
