import os, re
from bs4 import BeautifulSoup
import json
import time
import datetime
import util
import bisect
import copy

import numpy as np

MILS_TO_S = 1e3
DATES = {'янв':1, 'фев':2,'мар':3,'апр':4,'мая':5,'июн':6,
 'июл':7,'авг':8,'сен':9,'окт':10,'ноя':11,'дек':12}

class GKeepParse:
    def __init__(self, data_file=None):
        self.log = []
        self.read_data = []
        if data_file is not None:
            self.data_file = data_file



    def keep_parse(self, name='Keep', data_file=None):
        if data_file is None:
            data_file = self.data_file
        self.find_archive(name)
        self.log_from_keep()
        print(self.log)
        util.write_log_new(file=data_file,
                           logs=self.log,
                           new_t=util.get_last_date(data_file))


    def find_archive(self, name):
        for file in os.listdir(name):
            if file[-4:] == 'html':
                print(file)
                with open(name + '/' + file, 'r') as f:
                    self.read_data.append(f.read())
                f.closed

    def keep_date_normalize(self, lines_with_date):
        date = re.findall(string=str(lines_with_date), pattern='\d.*\d+:\d+:\d+')
        if len(date) == 0:
            return None
        date = date[0].split()
        date = (str(date[0]) + '/' + str(DATES[date[1][:3]]) + '/' + str(date[2]) +
                '/' + str(date[4])
                )
        dtime = time.mktime(datetime.datetime.strptime(date, "%d/%m/%Y/%H:%M:%S").timetuple())
        return dtime

    def log_from_keep(self):
        self.log = []
        for data in self.read_data:
            soup = BeautifulSoup(data, 'html.parser')
            date = self.keep_date_normalize(soup.title)
            if not date:
                date = self.keep_date_normalize(soup.div)
            body = soup.find_all(attrs={"class": "content"})
            body = body[0]
            self.log.append(util.add_to_log(source='Gkeep_arc', id='my', date=date,
                                  body=body.contents)
                       )


class GLocationParse:
    def __init__(self, file_loc_hist="Takeout/История "
                                     "местоположений/История "
                                     "местоположений.json"):
        self.data = []
        self.cur_data = []
        self.log = []
        if file_loc_hist is not None:
            with open(file_loc_hist, 'r') as f:
                self.data = json.loads(f.read())['locations']
            f.close()


    def precompute_data(self, need_sort=True):
        # change data inplace
        for point in self.data:
            point['timestampMs'] = int(point['timestampMs']) / MILS_TO_S  # to second
        if need_sort:
            self.data.sort(key=lambda x: x['timestampMs'])
        if len(self.data) > 1 and self.data[0]['timestampMs'] > self.data[1]['timestampMs']:
            self.data = list(reversed(self.data))
            # print (data[0], data_loc_hist[0])

    def get_time_key(self, data):
        return [x['timestampMs'] for x in data]

    def take_period(self, data, start="2013-04-02 4:00:00", end="2013-04-03 4:00:00"):
        # data sorted and reversed location old->new, with keys = [timestampMs, ]
        keys = self.get_time_key(data)
        start = util.time_str_to_int(start)
        end = util.time_str_to_int(end)
        i_start, i_end = bisect.bisect_left(keys, start), bisect.bisect_right(keys, end)
        print(i_start, i_end, end)
        return data[i_start:i_end]

    def log_from_loc_hist(self, glk_file="Log_raw/GLH_log.txt",
                          start_date="2000-01-21 16:20:20", end_date="2013-10-01"):
        self.precompute_data(self.data)
        # keys = get_time_key(data['locations'])
        self.cur_data = copy.deepcopy(self.take_period(self.data, start=start_date, end=end_date))
        self.add_vaules_to_cur_data()
        D = Day(data=self.cur_data)
        D.compres_data()
        for action in D.compressed_data:
            self.log.append(util.add_to_log(source="GLH", id="my", date=action['start_time'],
                                       body=action))
        util.write_log_new(file=glk_file, logs=self.log, new_t=util.get_last_date(glk_file))

    def grad_speed(self, a, b):
        S = util.getDistanceFromLatLonInKm(a['latitudeE7'] / 1e7, a['longitudeE7'] / 1e7,
                                      b['latitudeE7'] / 1e7, b['longitudeE7'] / 1e7)
        t = (int(b['timestampMs']) - int(a['timestampMs'])) / 3600
        if t:
            return S, t, S / t
        return 0, 0, 0



    #day = take_period(bskt_data, start="2013-04-02 4:00:00", end="2013-04-03 4:00:00")

    def add_vaules_to_cur_data(self):  # add next day
        #self.cur_data = copy.deepcopy(data_initial)
        for i in range(len(self.cur_data[:-1])):
            distant, t, speed = self.grad_speed(self.cur_data[i], self.cur_data[i + 1])
            self.cur_data[i]['grad_speed'] = speed
            self.cur_data[i]['distant'] = distant
            self.cur_data[i]['duration_s'] = (self.cur_data[i + 1]['timestampMs'] -
                                              self.cur_data[i]['timestampMs'])
        last_ind = len(self.cur_data) - 1
        self.cur_data[last_ind]['grad_speed'] = self.cur_data[last_ind - 1]['grad_speed']
        self.cur_data[last_ind]['duration_s'] = 20  # last duration
        self.cur_data[last_ind]['distant'] = distant

    def cur_data_stat(self):
        from collections import defaultdict
        k = defaultdict(lambda: 0)

        for p in self.cur_data:
            # print(p)
            if 'activity' in p:
                if len(p['activity']) > 1:
                    print(p['activity'])
                k[p['activity'][0]['activity'][0]['type']] += 1
            else:
                k['Noact'] += 1
            if p['grad_speed'] < 2:
                k['stable_'] += p['duration_s']
            if 2 <= p['grad_speed'] < 17:
                k['walk_run_b'] += p['duration_s']
            if p['grad_speed'] >= 17:
                k['transport'] += p['duration_s']
            k['ALL_TIME'] += p['duration_s']
            k['ALL_DISTANT'] += p['distant']
        k['ALL_POINTS'] = len(self.cur_data)
        print(k)

class Day:
    def __init__(self, data, last_compresed_action=None):
        # self.last_action = 'stable_'
        # self.last_point = last_point
        self.data = data
        self.compressed_data = []
        if last_compresed_action is not None:
            self.compressed_data.append(last_compresed_action)
            # self.activity_names = {}

    def compres_data(self):
        for point in self.data:
            if (len(self.compressed_data) > 0 and
                        self.get_action_type(point) == self.compressed_data[-1]['action_type']
                ):
                self.compressed_data[-1]['duration'] += point['duration_s']
                self.compressed_data[-1]['finish_loc'] = (point['latitudeE7'], point['longitudeE7'])
                self.compressed_data[-1]['distant'] += point['distant']
                self.compressed_data[-1]['n_points'] += 1
                # action['average_speed']
            else:
                # self.compressed_data[-1]['duration'] = point['duration_s']
                # self.compressed_data[-1]['finish_loc'] = (point['latitudeE7'], point['longitudeE7'])
                action = {}  # defaultdict(lambda: 0)
                action['start_time'] = point['timestampMs']
                action['start_loc'] = (point['latitudeE7'], point['longitudeE7'])
                action['finish_loc'] = None
                action['duration'] = point['duration_s']
                action['action_type'] = self.get_action_type(point)
                action['distant'] = point['distant']
                action['n_points'] = 1
                # action['average_speed'] = point['grad_speed']
                self.compressed_data.append(action)
                # self.last_point = point

    def get_action_type(self, point):
        if point is None:
            return '-1'
        # if point['move_forward'] < 0:
        #    print (point['grad_speed'], point['timestampMs'])
        #    k['returns_point'] += 1
        if 0 <= point['grad_speed'] < 2:
            return 'stable_'
        if 2 <= point['grad_speed'] < 17:
            return 'walk_run_b'
        if point['grad_speed'] >= 17:
            return 'transport'
            # print('---', point['grad_speed'])



    #cd = add_vaules_to_data(day)


class GSearchParse:

    def __init__(self, data_file='Takeout/Мои действия/Поиск/МоиДействия.html'):
        self.data_file = data_file
        with open(data_file, 'r') as f:
            self.html_dt = f.read()
            f.close()

        self.log = []

    # re.findall(string=html_dt[:150000], pattern='Поиск')
    #DATES = {'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'мая': 5, 'июн': 6,
    #         'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12}

    def gsearch_date_normalize(self, lines_with_date):
        # make one for all classes Keep&Search&Android
        date = re.findall(string=str(lines_with_date), pattern='<br>\d.*\d+:\d+:\d+')
        if len(date) == 0:
            return None

        if len(date[0]) > 32: #we '<br>11\xa0подсказок<br>16 мая 2018 г., 23:37:28' find this-cut one br
            #print("--", date[0][-32:], len(date[0]))
            date = re.findall(string=date[0][-32:], pattern='<br>\d.*\d+:\d+:\d+')
        #print(date)#, len(date[0]))
        date = date[0][4:].split()
        date = (str(date[0]) + '/' + str(DATES[date[1][:3]]) + '/' + str(date[2]) +
                '/' + str(date[4])
                )
        dtime = time.mktime(datetime.datetime.strptime(date, "%d/%m/%Y/%H:%M:%S").timetuple())
        return dtime

    def log_from_gsearch(self):
        string = self.html_dt.split('class')
        print("search {}".format(self.data_file))
        print("find {} clasess".format(len(string)))
        for i in string:#
            line = (re.findall(string=i, pattern='[А-Яа-я].*\d+:\d+:\d+'))
            if line:
                date = self.gsearch_date_normalize(line[0])
                quory = re.findall(string=i, pattern='\w.?q=.*".*</a>')
                if not quory:
                    body = {'type': 'other', 'url': '', 'text': ''}
                    self.log.append(util.add_to_log(date=date, source='GSearch', id='my', body=body))
                else:
                    url, text = quory[0][3:].split('\">')
                    body = {'type': quory[0][0], 'url': url, 'text': text[:-4]}
                    self.log.append(util.add_to_log(date=date, source='GSearch', id='my', body=body))
        print("finish with {} clasess".format(len(self.log)))
        print("start {} - end {} ".format(util.time_int_to_str(self.log[0]["date"]),
                                          util.time_int_to_str(self.log[-1]["date"])
                                          ))

    def write_log(self, log_file="Log_raw/GSearch_log.txt"):
        print(len(self.log))
        util.write_log_new(file=log_file, logs=self.log,
                           new_t=util.get_last_date(log_file))


class Android(GSearchParse):
    # TODO make interface for parsers
    def __init__(self, data_file="Takeout/Мои действия/Android/МоиДействия.html"):
        self.data_file = data_file;
        with open(data_file, 'r') as f:
            self.html_dt = f.read()
            f.close()
        self.log = []

    def log_from_android(self):
        string = self.html_dt.split('class')
        print("Android {}".format(self.data_file))
        print("find {} clasess".format(len(string)))

        for i in string:
            line = (re.findall(string=i, pattern='[А-Яа-я].*\d+:\d+:\d+'))

            if line:
                # print(line)
                date = self.gsearch_date_normalize(line[0])
                applink = re.findall(string=i, pattern='&nbsp;<a.*".*</a>')
                apponly = re.findall(string=i, pattern='&nbsp;.*[^(</a>)]<br>')
                body = None
                if applink:
                    applink = applink[0][15:-4].split('">')
                    body = {'applink': applink[0], 'app': applink[1]}
                if apponly:
                    body = {'app': apponly[0][6:-4]}
                if body:
                    self.log.append(util.add_to_log(date=date, source='Android', id='my', body=body))
        print("finish with {} clasess".format(len(self.log)))
        print("start {} - end {} ".format(util.time_int_to_str(self.log[0]["date"]),
                                          util.time_int_to_str(self.log[-1]["date"])
                                          ))


    #log_from_gsearch(html_dt[:150000])

if __name__ == "__main__":
    #k = GKeepParse(data_file="/Test/t_keep.txt")
    #k.keep_parse(name="Test/TKeep", data_file='Test/t_keep.txt')

    g = GLocationParse()
    g.log_from_loc_hist(end_date="2018-10-03 4:00:00")

    #s = GSearchParse()
    #s.log_from_gsearch()
    #s.write_log()

    #a = Android()
    #a.log_from_android()
    #a.write_log(log_file="Log_raw/Android_log.txt")