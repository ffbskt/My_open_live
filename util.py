import json
import datetime
import math

def add_to_log(source, id, date, body):
    log = ({"source":source, "user_id":str(id), "date":date,
            "body":body})
    return log

def get_all_message(file_adr):
    """
    Read parsed file // 'Log_raw/Gkeep_arc.txt'
    :param file_adr:
    :return: text
    """

    #'Log_raw/Gkeep_arc.txt'):
    with open(file_adr, 'r') as dt:
        all_mes = dt.read()
        dt.close()
        return all_mes

def get_last_date(file):
    try:
        last_line = (get_all_message(file_adr=file).split('\n')[-2])
        return json.loads(last_line)['date']
    except IndexError:
        return 0

def write_log_new(file, logs=None, new_t=0):
    """
    write log as json to txt newer then time new_t
    :param file:
    :param logs: list of dict
    :param new_t:
    :return:
    """
    with open(file, 'a') as dt:
        for log in logs:
            try:
                if log['date'] > new_t:
                    #print(log())
                    dt.write(json.dumps(log, sort_keys=True) + '\n')
            except TypeError:
                pass
        dt.close()

def time_str_to_int(t):
    # return seconds
    if ":" in t:
        d = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S").timestamp()
    else:
        d = datetime.datetime.strptime(t, "%Y-%m-%d").timestamp()
    return d  # * MILS_TO_S

def time_int_to_str(t):
    # t seconds
    return datetime.datetime.fromtimestamp(t)

def getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2):
    # Copyright 2012-2017 Gerwin Sturm
    R = 6371  # Radius of the earth in km
    dlat = deg2rad(lat2 - lat1)
    dlon = deg2rad(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
        math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * \
        math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c  # Distance in km
    return d

def deg2rad(deg):
    return deg * (math.pi / 180)
