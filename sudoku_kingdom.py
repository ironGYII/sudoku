# -*- coding: utf-8 -*-

import time
import commandr
import requests
import traceback
from functools import partial

from queue import Queue, Empty
from threading import Thread
from throttle import Throttle
from sudoku_spider import WriteResult, lazy_property


def worker(work_queue, throttle, func, write_result_obj):

    while True:

        try:
            level = work_queue.get(block=False)
        except Empty:
            break

        while not throttle.consume(1):
            pass
        value = func(level)

        try:
            if value is not None:
                game_id, _level, result_id = value
                write_result_obj.success(game_id, _level, result_id)
        except Exception as e:
            print(traceback.format_exc())
            break


class CacheWriteResult(WriteResult):

    def __init__(self, task_name, aim_count):
        super(CacheWriteResult, self).__init__(task_name=task_name)
        self.aim_count = aim_count
        self._cache_index = set([])

    def success(self, game_id, level, result_id):
        if len(self._cache_index) >= self.aim_count:
            raise Exception('spider count enough')

        if game_id in self._cache_index:
            return

        self._cache_index.add(game_id)
        super(CacheWriteResult, self).success(game_id, level, result_id)


class SudokuKingdom(object):

    host = 'https://www.sudokukingdom.com/index.php'

    headers = {'Host': 'www.sudokukingdom.com',
               'Origin': 'https://www.sudokukingdom.com',
               'Referer': 'https://www.sudokukingdom.com/very-easy-sudoku'}

    level_map = {1: 'very_easy', 2: 'medium', 3: 'difficult', 4: 'very_difficult'}

    def __init__(self, level):
        self.level = level

    @property
    def _params(self):
        return {'t': int(time.time() * 1000), 'y': ' f2 ', 'w': 'bz', 'l': self.level}

    @lazy_property
    def resp(self):
        resp = requests.post(self.host, headers=self.headers, params=self._params)
        return resp.text

    @property
    def result(self):
        _, _, dirty_result, _, _ = self.resp.split('@')
        result = [char if char.isdigit() else '0' for char in dirty_result]
        return ''.join(result)

    @property
    def index(self):
        _, index, _, _, _ = self.resp.split('@')
        return index

    @classmethod
    def run(cls, level):

        try:
            obj = cls(level)
            index = obj.index
            result_id = obj.result
            return index, cls.level_map[level], result_id
        except Exception as e:
            print(traceback.format_exc())


@commandr.command('sudoku_kingdom')
def download_sudoku_kingdom(level=1, count=1000, thread_count=20):
    write_result_obj = CacheWriteResult(task_name='sudoku_kingdom', aim_count=count)
    throttle = Throttle(1, 10)
    work_queue = Queue()
    for i in range(0, count * 100):
        work_queue.put(level)

    threads = [Thread(target=worker, args=(work_queue, throttle, SudokuKingdom.run, write_result_obj)) for _ in range(thread_count)]

    for thread in threads:
        thread.start()

    while threads:
        threads.pop().join()


if __name__ == '__main__':
    commandr.Run()
