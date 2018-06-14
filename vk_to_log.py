import requests
import vk_api
import time
import util
import json



class VkArchive:
    def __init__(self, login, password):
        """
        vk log and pass to init vk_api
        :param login: vk log
        :param password: vk pass
        """
        self.MYID = 161389333
        #session = requests.Session()
        self.MAXC = 200
        vk_session = vk_api.VkApi(login, password)
        try:
            vk_session.auth()
        except vk_api.AuthError as error_msg:
            print(error_msg)

        self.vk = vk_session.get_api()


    def encrypt_vkid(self, id, vk_api):
        name = vk_api.users.get(user_ids=id)[0]
        n, s = name['first_name'][1], name['last_name'][1:3]
        xid = (id + 10001) * 5
        return n + s + str(xid)

    def decrypt_vkid(self, idx):
        return int(idx[3:]) // 5 - 10001



    def get_id_from_dialogs(self, dialogs):
        ids = []
        for d in dialogs['items']:
            ids.append(d['message']['user_id'])
        return ids

    def get_full_conv(self, id, vk_api):
        n = self.vk.messages.getHistory(user_id=id)['count']
        full_conv = []
        i = 0
        while i < n:
            time.sleep(0.3)
            m = self.vk.messages.getHistory(offset=i, count=self.MAXC, user_id=id)
            full_conv.extend(m['items'])
            # print()
            i += self.MAXC
        return full_conv

    def log_from_vk(self):
        n = self.vk.messages.getDialogs()['count']
        log = []
        i = 0
        while i < n:
            time.sleep(0.3)
            dialogs = self.vk.messages.getDialogs(offset=i, count=self.MAXC)
            ids = self.get_id_from_dialogs(dialogs)
            i += self.MAXC
            for id in ids:
                full_conv = self.get_full_conv(id, self.vk)
                log.extend(self.message_to_log(full_conv))

                # !! get last date take any date even from other dialogs
                util.write_log_new(file='Log_raw/vk_log.txt', logs=log, new_t=util.get_last_date('Log_raw/vk_log.txt'))
                # print(i, ids[:10], len(ids))


#log_from_vk()



#s = get_full_conv(10882721, vk)


    def message_to_log(self, full_conv):
        log = []
        user = self.encrypt_vkid(full_conv[0]['user_id'], vk)
        for mes in full_conv:
            to, fr = user, user
            if mes['from_id'] == mes['user_id']:
                to = self.MYID
            else:
                fr = self.MYID
            body = {
                'from': fr,
                'to': to,
                'text': mes['body']
            }
            log.append(util.add_to_log(
                source='vk', id=self.MYID, date=mes['date'], body=body
            ))
        return log

#d = message_to_log(s)
#len(d), d[:3]

if __name__ == "__main__":
    with open("/home/denis/sensitive_data.py", "r") as f:
        VK = json.loads(f.read())['VK']
        f.close()

    arch = VkArchive(VK["log"], VK["pass"])
    print(VK)