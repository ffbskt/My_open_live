import os, re
from bs4 import BeautifulSoup
import json
import time
import datetime
import util
DATES = {'января':1, 'февраля':2,'марта':3,'апреля':4,'мая':5,'июня':6,
 'июля':7,'августа':8,'сентября':9,'октября':10,'ноября':11,'декабря':12}

class GArchiveParse:
    def __init__(self, data_file=None):
        self.log = []
        self.read_data = []
        if data_file is not None:
            self.data_file = data_file
        # else create



    def keep_parse(self, name='Keep', data_file=None):
        if data_file is None:
            data_file = self.data_file
        self.find_archive(name)
        self.log_from_keep()
        print(self.log)
        util.write_log_new(file=data_file,
                           logs=self.log,
                           new_t=util.get_last_date(data_file))

    def map_parse(self):
        pass

    def get_last_date(self):
        pass

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
        date = (str(date[0]) + '/' + str(DATES[date[1]]) + '/' + str(date[2]) +
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





if __name__ == "__main__":
    a = GArchiveParse(data_file="/Test/t_keep.txt")
    a.keep_parse(name="Test/TKeep", data_file='Test/t_keep.txt')