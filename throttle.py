# -*- coding: utf-8 -*-

import time
from threading import Lock, Thread
from queue import Queue, Empty


class Throttle(object):

    """
    线程安全的限速类, 使用方式:
    throttle = Throttle(10, 100) # 10s中内提供100次可以执行数

    线程中使用:
        throttle.consume(n)
    """

    def __init__(self, time_period, count_per_period):
        """
        :param time_period: 分片的时间段长度, 单位是秒
        :param count_per_period: 每个分片提供可用数量
        """
        self._consume_lock = Lock()

        self.period = time_period
        self.rate = count_per_period

        self.available_counts = 0
        self.last_time = 0
        self.all_count = 0

    def consume(self, amount):
        with self._consume_lock:
            now = time.time()

            # 时间测量在第一令牌请求上初始化以避免初始突发
            if self.last_time == 0:
                self.last_time = now
                self.available_counts = self.rate

            elapsed = now - self.last_time

            if elapsed > self.period:
                self.available_counts = self.rate
                self.last_time = now

            # 如果可用最终分派令牌
            if self.available_counts >= amount:
                self.available_counts -= amount
                self.all_count += amount
            else:
                amount = 0

            return amount


