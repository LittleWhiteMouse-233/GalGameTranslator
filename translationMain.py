# 爬虫-翻译器核心
import abc
import hashlib
import json
import os
import random
import threading
import time
import warnings

import requests

import myLog
import utils
from utils import file2dict, xls2dict, file2list

warnings.filterwarnings('always')


class TranslationTask(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_input_from_to_use(self): ...

    @abc.abstractmethod
    def set_output(self, pkg): ...

    @abc.abstractmethod
    def after_translate(self, change, pkg): ...


class TranslationCore:
    API_DIR = 'api'
    API_LIST = 'api_list.txt'
    __task_dict = dict()
    use_dict = dict()
    running = False
    running_sleep = 1
    Thread = None
    cache = []
    Lock = threading.Lock()
    logger = myLog.LoggerCreator.get_default_logger(name='TranslationCore')

    def __init__(self, use: str = 'baidu'):
        self.use_list = file2list(os.path.join('.', self.API_DIR, self.API_LIST))
        self.__add_use(use)
        self.init_dict = {
            'from': self.use_dict[use]['from'].keys(),
            'by': self.use_list,
            'to': self.use_dict[use]['to'].keys()
        }

    def add_translate_task(self, task: TranslationTask, task_id: int = None):
        max_len = 100
        if task_id is None:
            for task_id in range(max_len):
                if task_id not in self.__task_dict.keys():
                    break
        self.logger.info("Adding translate task %s ...", str(task_id))
        if len(self.__task_dict) >= max_len:
            self.logger.warning("Add task failed, There is too many tasks.")
            return False
        if task_id in self.__task_dict.keys():
            self.logger.warning("Add task failed, the task_id: %s is existed.", str(task_id))
            return False
        self.Lock.acquire()
        self.cache.append((1, (task, task_id)))
        self.Lock.release()
        return task_id

    def remove_translate_task(self, task_id: int):
        self.logger.info("Removing translate task %s ...", str(task_id))
        if task_id not in self.__task_dict.keys():
            self.logger.warning("Remove failed, the task_id: %s is not existed.", str(task_id))
            return False
        self.Lock.acquire()
        self.cache.append((-1, (task_id,)))
        self.Lock.release()
        return True

    def __add_translate_task(self, task: TranslationTask, task_id: int):
        self.__task_dict[task_id] = {
            'task': task,
            'last': task.get_input_from_to_use(),
        }
        self.logger.info("Add task %d successfully. Current tasks list: %s, count: %d.",
                         task_id, str(self.__task_dict.keys()), len(self.__task_dict))

    def __remove_translate_task(self, task_id: int):
        self.__task_dict.pop(task_id)
        self.logger.info("Remove task %d successfully. Current tasks list: %s, count: %d.",
                         task_id, str(self.__task_dict.keys()), len(self.__task_dict))

    def __operate_all(self):
        self.Lock.acquire()
        for _ in range(len(self.cache)):
            op_code, op_pkg = self.cache.pop()
            if op_code == 1:
                self.__add_translate_task(*op_pkg)
            elif op_code == -1:
                self.__remove_translate_task(*op_pkg)
            else:
                self.logger.error("Invalid operation.")
        self.Lock.release()

    def check_task_exist(self, task_id: int):
        return task_id in self.__task_dict.keys()

    def start_translate(self):
        self.logger.info("Translate thread starting ...")
        self.running = True
        self.Thread = threading.Thread(target=self.__translate_all)
        self.Thread.setName('TranslateCore')
        self.Thread.setDaemon(True)
        self.Thread.start()
        self.logger.info("Translate thread is running.")

    def shutdown_translate(self):
        self.logger.info("Translate thread quiting ...")
        self.running = False
        if self.Thread.is_alive():
            self.Thread.join()
        self.logger.info("Translate thread shutdown.")

    def __translate_all(self):
        runtimes = 0
        while True:
            if runtimes >= 10000:
                runtimes = 0
            runtimes += 1
            if not self.running:
                break
            # 遍历循环翻译
            for task_id in self.__task_dict.keys():
                task_pkg = self.__task_dict[task_id]
                task: TranslationTask = task_pkg['task']
                if runtimes % 10 == 1:
                    self.logger.debug("Task %d get ...", task_id)
                new = task.get_input_from_to_use()
                change = self.__check_change(new, task_pkg['last'])
                if any(change):
                    pkg = self.translate(*new)
                    task.set_output(pkg)
                    task.after_translate(change, pkg)
                    task_pkg['last'] = new
                    self.logger.info("Translate result: %s -> %s.", str(new), str(pkg))
                    time.sleep(0.5)
            t = threading.Thread(target=self.__operate_all)
            t.setDaemon(True)
            t.start()
            time.sleep(self.running_sleep)
            if t.is_alive():
                t.join()

    def __check_change(self, new: tuple, last: tuple):
        if len(new) != 4 or len(last) != 4:
            self.logger.warning("The len(new) or len(last) should be 4, please check task.get_input_from_to_use().")
            return [False, ] * 4
        change = [False, ] * 4
        for i, s in enumerate(new):
            if type(s) != str:
                self.logger.warning("%s should be str type, please check task.get_input_from_to_use().", str(s))
                return [False, ] * 4
            change[i] = (s.strip() != last[i].strip())
        return change

    def translate(self, query: str, from_lang: str = '', to_lang: str = '', use: str = ''):
        if not query.strip():
            return ''
        if use.strip():
            use = self.__add_use(use)
        try:
            if use == 'baidu' or not use.strip():
                return self.__translate_baidu(query, from_lang, to_lang)
            else:
                self.logger.warning("There is not function by %s", str(use))
                return self.__translate_baidu(query, from_lang, to_lang)
        except requests.exceptions.RequestException as e:
            self.logger.error("Translate failed. " + str(e))
            return None, from_lang, to_lang, use

    def __add_use(self, use: str):
        if use not in self.use_dict.keys():
            if use not in self.use_list:
                self.logger.warning("Can not find this use in %s: %s", self.API_LIST, str(use))
                return ''
            self.use_dict[use] = {
                'from': xls2dict(os.path.join('.', self.API_DIR, use + '_from.xls')),
                'to': xls2dict(os.path.join('.', self.API_DIR, use + '_to.xls')),
                'info': file2dict(os.path.join('.', self.API_DIR, use + '.txt')),
            }
        return use

    def __check_from_to(self, from_lang: str, to_lang: str, use: str):
        def check(a: str, dic: dict):
            if a.strip():
                if not utils.in_english(a):
                    if a in dic.keys():
                        return a, dic[a]
                    else:
                        self.logger.warning("Unexpected from_lang or to_lang in Chinese: %s", str(a))
                else:
                    if a in dic.values():
                        return list(dic.keys())[list(dic.values()).index(a)], a
                    else:
                        self.logger.warning("Unexpected from_lang or to_lang in English: %s", str(a))
            return list(dic.keys())[0], list(dic.values())[0]

        return check(from_lang, self.use_dict[use]['from']), check(to_lang, self.use_dict[use]['to'])

    def __translate_baidu(self, query: str, from_lang: str, to_lang: str):
        use = 'baidu'
        from_lang_ce, to_lang_ce = self.__check_from_to(from_lang, to_lang, use)
        from_lang = from_lang_ce[1]
        to_lang = to_lang_ce[1]
        info_dict = self.use_dict[use]['info']
        salt = str(random.randint(32768, 65536))
        sign = hashlib.md5((info_dict['appid'] +
                            query +
                            salt +
                            info_dict['appkey']).encode('utf-8')).hexdigest()
        # Build request
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'appid': info_dict['appid'],
                   'q': query,
                   'from': from_lang,
                   'to': to_lang,
                   'salt': salt,
                   'sign': sign}
        # Send request
        r = requests.post(info_dict['url'], params=payload, headers=headers)
        result = r.json()
        # Show response
        if __name__ == '__main__':
            print(json.dumps(result, indent=4, ensure_ascii=False))
        keyname = 'trans_result'
        translate_result = ''
        if keyname in result.keys():
            for paragraph in result[keyname]:
                translate_result = translate_result + paragraph['dst'] + '\n'
            return translate_result, from_lang_ce[0], to_lang_ce[0], use
        else:
            self.logger.error('Translate failed. Invalid key.')
            return None, from_lang_ce[0], to_lang_ce[0], use


# 测试
if __name__ == '__main__':
    translator = TranslationCore('baidu')
    while True:
        inputStr = ''
        print('请输入要翻译的内容：')
        while True:
            inputStr = inputStr + input() + '\n'
            if (inputStr[-3:] == 'hs\n') or (inputStr[-3:] == 'HS\n'):
                break
        if inputStr[-3:] == 'HS\n':
            break
        print("翻译的结果为：\n" + translator.translate(inputStr[:-3]))
