import json

def add_to_log(source, id, date, body):
    log = ({"source":source, "user_id":str(id), "date":date,
            "body":str(body)})
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
            if log['date'] > new_t:
                dt.write(json.dumps(log, sort_keys=True) + '\n')
        dt.close()