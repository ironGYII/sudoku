# -*- coding: utf-8 -*-
import commandr
import requests
from threading import Thread, Lock
from queue import Queue, Empty
from bs4 import BeautifulSoup
from throttle import Throttle
import traceback


class lazy_property(object):

    def __init__(self, func):

        self.fget = func

    def __get__(self, instance, owner):
        value = self.fget(instance or owner)
        setattr(instance, self.fget.__name__, value)
        return value


class WriteResult(object):

    def __init__(self, task_name):
        self.success_lock = Lock()
        self.failed_lock = Lock()
        self.task_name = task_name

    def success(self, game_id, level, result_id):
        with self.success_lock:
            with open('out/{}_success.txt'.format(self.task_name), 'a') as f:
                f.write(str(game_id)+ '    ' + level + '    ' + result_id + '\n')

    def failed(self, game_id):
        with self.failed_lock:
            with open('out/{}_failed.txt'.format(self.task_name), 'a') as f:
                f.write(str(game_id) + '\n')


class SudokuNow(object):

    _url = "https://www.sudokunow.com/{game_id}"

    level_map = {1: 'very_easy', 2: 'easy', 3: 'medium', 4: 'difficult', 5: 'very_difficult'}

    def __init__(self, game_id):
        self.game_id = game_id

    @lazy_property
    def table(self):
        response = requests.get(self._url.format(game_id=self.game_id))
        soup = BeautifulSoup(response.text)
        return soup.table

    @property
    def level(self):
        thead = self.table.thead

        level_objs = thead.find_all('a')

        levels = set([])
        for level_obj in level_objs:
            _level = level_obj['href'].split('/')[-1]
            if level_obj.i.attrs['class'][-1] == 'sudoku-active':
                levels.add(_level)
        return self.level_map[len(levels)]

    @property
    def result(self):

        game_id = []

        for tr in self.table.tbody.find_all('tr'):
            for td in tr.find_all('td'):
                _value = td.span.text
                _value = _value if len(_value) > 0 else '0'
                game_id.append(_value)
        return ''.join(game_id)

    @classmethod
    def run(cls, game_id):
        obj = cls(game_id)
        try:
            level = obj.level
            result_id = obj.result
            return level, result_id
        except Exception as e:
            print(traceback.format_exc())


class Sudoku9x9(object):

    host = 'https://sudoku9x9.com/'
    level_map = {1: 'very_easy', 2: 'easy', 3: 'medium', 4: 'difficult', 5: 'very_difficult'}

    def __init__(self, level, index):

        """

        :param level: 1 最简单  ~ 5 最难
        :param index: 游戏在当前难度下的索引, int值, 据网站上说,有几百万的内容。
        """
        self.level = level
        self.headers = {'cookie': 'level={}'.format(level)}
        self.params = {'puzzleno': index, 'pickgame': 'Go'}

    @lazy_property
    def table(self):
        response = requests.post(self.host, data=self.params, headers=self.headers)
        html = response.text
        soup = BeautifulSoup(html)
        table = soup.find('div', id='playtable')
        return table

    @property
    def result(self):
        result = [0] * 81
        for _div in self.table.find_all('div'):
            if 'id' in _div.attrs and _div.attrs['id'].startswith('cell'):
                position = _div.attrs['id'][4:]
                value = _div.textarea.text
                value = value if len(value) == 1 else '0'
                result[int(position)] = value
        return ''.join(result)

    @classmethod
    def run(cls, index, level):
        obj = cls(index=index, level=level)
        try:
            level = obj.level
            result_id = obj.result
            return cls.level_map[level], result_id
        except Exception as e:
            print(traceback.format_exc())


def worker(work_queue, throttle, func, write_result_obj):

    while True:

        try:
            game_id = work_queue.get(block=False)
        except Empty:
            break

        while not throttle.consume(1):
            pass
        value = func(game_id)

        try:
            if value is None:
                write_result_obj.failed(game_id)
            else:
                level, result_id = value
                write_result_obj.success(game_id, level, result_id)
        except Exception as e:
            print(traceback.format_exc())
            break


@commandr.command('sudokunow')
def download_sudokunow(thread_count=20):

    write_result_obj = WriteResult(task_name='sudokunow')
    throttle = Throttle(1, 10)
    work_queue = Queue()
    for i in range(0, 1000):
        work_queue.put(i)

    threads = [Thread(target=worker, args=(work_queue, throttle, SudokuNow.run, write_result_obj)) for _ in range(thread_count)]

    for thread in threads:
        thread.start()

    while threads:
        threads.pop().join()


@commandr.command('sudoku9x9')
def download_sudoku9x9(thread_count=20, level=1):

    write_result_obj = WriteResult(task_name='sudoku9x9')
    throttle = Throttle(1, 10)
    work_queue = Queue()
    for i in range(0, 1000):
        work_queue.put(i)
    from functools import partial
    func = partial(Sudoku9x9.run, level=level)
    threads = [Thread(target=worker, args=(work_queue, throttle, func, write_result_obj)) for _ in range(thread_count)]

    for thread in threads:
        thread.start()

    while threads:
        threads.pop().join()


if __name__ == '__main__':
    commandr.Run()
