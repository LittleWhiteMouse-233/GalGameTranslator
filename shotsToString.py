import abc
import os.path
import threading
import time

import pytesseract
from PIL import Image, ImageGrab

import myLog
import utils


class ShotToStringTask:
    @abc.abstractmethod
    def get_bbox_lang(self): ...

    @abc.abstractmethod
    def set_content(self, text): ...


class Shots2String:
    API_DIR = 'api'
    API_LANG = 'tesseract_lang.xls'
    __shots_dict = dict()
    running = False
    running_sleep = 1
    Thread = None
    cache = []
    Lock = threading.Lock()
    logger = myLog.LoggerCreator.get_default_logger(name='Shots2String')
    pytesseract.pytesseract.tesseract_cmd = utils.file2list(os.path.join(API_DIR, 'tesseract_path.txt'))[0]

    def __init__(self):
        self.lang_dict = utils.xls2dict(os.path.join('.', self.API_DIR, self.API_LANG))

    def add_shot(self, task: ShotToStringTask, shot_id: int = None):
        max_len = 100
        if shot_id is None:
            for shot_id in range(max_len):
                if shot_id not in self.__shots_dict.keys():
                    break
        self.logger.info("Adding shot %s ...", str(shot_id))
        if len(self.__shots_dict) >= max_len:
            self.logger.warning("Add shot failed, there is too many shots.")
            return False
        if shot_id in self.__shots_dict.keys():
            self.logger.warning("Add shot failed, the shot_id: %s is existed.", str(shot_id))
            return False
        self.Lock.acquire()
        self.cache.append((1, (task, shot_id)))
        self.Lock.release()
        return shot_id

    def remove_shot(self, shot_id: int):
        self.logger.info("Removing shot %s ...", str(shot_id))
        if shot_id not in self.__shots_dict.keys():
            self.logger.warning("Remove failed, the shot_id: %s is not existed.", str(shot_id))
            return False
        self.Lock.acquire()
        self.cache.append((-1, (shot_id,)))
        self.Lock.release()
        return True

    def update_shot(self, task: ShotToStringTask, shot_id: int):
        self.logger.info("Updating shot %s ...", str(shot_id))
        if shot_id not in self.__shots_dict.keys():
            self.logger.warning("Update shot failed, the shot_id: %s is not existed.", str(shot_id))
            return False
        self.Lock.acquire()
        self.cache.append((0, (task, shot_id)))
        self.Lock.release()
        return True

    def __add_shot(self, task: ShotToStringTask, shot_id: int):
        self.__shots_dict[shot_id] = task
        self.logger.info("Add shot %d successfully. Current shots list: %s, count: %d.",
                         shot_id, str(self.__shots_dict.keys()), len(self.__shots_dict))

    def __remove_shot(self, shot_id: int):
        self.__shots_dict.pop(shot_id)
        self.logger.info("Remove shot %d successfully. Current shots list: %s, count: %d.",
                         shot_id, str(self.__shots_dict.keys()), len(self.__shots_dict))

    def __update_shot(self, task: ShotToStringTask, shot_id: int):
        self.__shots_dict[shot_id] = task
        self.logger.info("Update shot %d successfully.", shot_id)

    def __operate_all(self):
        self.Lock.acquire()
        for _ in range(len(self.cache)):
            op_code, op_pkg = self.cache.pop()
            if op_code == 1:
                self.__add_shot(*op_pkg)
            elif op_code == -1:
                self.__remove_shot(*op_pkg)
            elif op_code == 0:
                self.__update_shot(*op_pkg)
            else:
                self.logger.error("Invalid operation.")
        self.Lock.release()

    def check_shot_exist(self, shot_id: int):
        return shot_id in self.__shots_dict.keys()

    def start_s2s(self):
        self.logger.info("Shots to string thread starting ...")
        self.running = True
        self.Thread = threading.Thread(target=self.__shots_to_string)
        self.Thread.setName('Shots2String')
        self.Thread.setDaemon(True)
        self.Thread.start()
        self.logger.info("Shots to string thread is running.")

    def shutdown_s2s(self):
        self.logger.info("Shots to string thread quiting ...")
        self.running = False
        if self.Thread.is_alive():
            self.Thread.join()
        self.logger.info("Shots to string thread shutdown.")

    def __shots_to_string(self):
        runtimes = 0
        while True:
            if runtimes >= 10000:
                runtimes = 0
            runtimes += 1
            if not self.running:
                break
            for shot_id in self.__shots_dict.keys():
                shot: ShotToStringTask = self.__shots_dict[shot_id]
                bbox, lang = shot.get_bbox_lang()
                if bbox is None or lang is None:
                    continue
                content = self.shot_to_string(bbox, lang)
                if runtimes % 10 == 1:
                    self.logger.debug('Shot %d get: %s.', shot_id, content.replace('\n', ' '))
                shot.set_content(content)
            t = threading.Thread(target=self.__operate_all)
            t.setDaemon(True)
            t.start()
            time.sleep(self.running_sleep)
            if t.is_alive():
                t.join()

    def shot_to_string(self, bbox: tuple[int, int, int, int], lang: str):
        lang = self.__check_lang(lang)
        if lang == '':
            lang = None
        string = pytesseract.image_to_string(self.__get_shot_image(bbox), lang=lang)
        if __name__ == '__main__':
            print(string)
        return string

    def __check_lang(self, lang: str):
        def check(a: str, dic: dict):
            if not a.strip():
                return ''
            if not utils.in_english(a):
                if a in dic.keys():
                    return dic[a]
                else:
                    self.logger.warning("Unexpected lang in Chinese: %s", str(a))
                    return ''
            else:
                if a in dic.values():
                    return a
                else:
                    self.logger.warning("Unexpected lang in English: %s", str(a))
                    return ''

        return check(lang, self.lang_dict)

    @staticmethod
    def __get_shot_image(bbox: tuple[int, int, int, int] = None):
        return ImageGrab.grab(bbox)

    @staticmethod
    def __save_image(image: Image):
        image.save(time.strftime('%H_%M_%S.png'))

    def screenshot(self):
        self.__save_image(self.__get_shot_image())


if __name__ == '__main__':
    s2s = Shots2String()
    s2s.screenshot()
