import pandas as pd
import numpy as np
import datetime
import time
import Queue

from abc import ABCMeta, abstractmethod

class TimeManager(object):
	__metaclass__ = ABCMeta

	@abstractmethod
	def sleepUntilNextTimeIndex(self, symbol, amount, type="MARKET"):
		raise NotImplementedError("Should implement execute_order()")



class Forex_Time_Manager(TimeManager):
	def __init__(self, start=None, end=None, duration=None, freq="5S"):
		self.freq = freq

		self.start = start
		if self.start == None:
			self.start = self.round_time_up(self.get_real_time(), freq)

		self.timeindex = self.start

		self.end = end
		if self.end == None:
			if duration == None:	#default to the next saturday
				self.end = self.start
				while self.end.weekday() != 5: #5 for saturday
					self.end += datetime.timedelta(days=1)
			else:
				self.end = self.get_next_time(duration)

		self.market_times = self.generate_trading_times()

		self.timeindex = self.market_times.next()
		self.next_timeindex = self.market_times.next()

		self.islive = self.next_timeindex >= self.get_real_time()
		self.iscontinue = True

	def sleepUntilNextTimeIndex(self):
		#sleep until next timestep
		total_seconds = (self.next_timeindex - self.get_real_time()).total_seconds()
		time.sleep(max(total_seconds,0))

		#check if system is running on live data
		##how to ensure that time is correct with real time
		self.timeindex = self.next_timeindex
		self.next_timeindex = self.market_times.next()

		self.real_start_time = self.get_real_now() #for backtest to ensure code runs inside timestep

		#check if system is at the end of test
		if self.next_timeindex > self.end:
			self.iscontinue = False

	def generate_trading_times(self):
		datetimes = pd.date_range(self.start, self.end, self.freq)
		datetimes = datetimes[not (datetimes.weekday == 5
							  or (datetimes.weekday == 6 and datetimes.hour < 17)
							  or (datetimes.weekday == 4 and datetimes.hour > 16))]
		for dt in datetimes:
			yield dt

	def now(self):
		if self.islive:
			#return real time
			return self.get_real_time()
		else:
			#return simulated time
			return self.timeindex + (self.get_real_time() - self.real_start_time)

	def get_real_time(self):
		#return real time
		return pd.to_datetime(datetime.datetime.utcnow())

	def get_next_time(self, freq):
		#get next market time rounded to correct freq
		step = freq[-1]
		num = freq[:-1]
		timetemp = self.timeindex
		if len(num) == 0:
			num = 1
		else:
			num = int(num)
		if step == "T":
			delta = datetime.timedelta(minutes=num)
		elif step == "S":
			delta = datetime.timedelta(seconds=num)
		elif step == "H":
			delta = datetime.timedelta(hours=num)
		elif step == "D":
			delta = datetime.timedelta(days=num)

		timetemp += delta

		return timetemp

	def round_time_down(self, time, freq):
		step = freq[-1]
		num = freq[:-1]
		if step == "S":
			time -= datetime.timedelta(seconds=time.seconds%num, milliseconds=time.milliseconds)
		elif step == "T":
			time -= datetime.timedelta(minutes=time.minutes%num, seconds=time.seconds, milliseconds=time.milliseconds)
		elif step == "H":
			time -= datetime.timedelta(hours=time.hours%num, minutes=time.minutes, seconds=time.seconds, milliseconds=time.milliseconds)
		elif step == "D":
			time -= datetime.timedelta(hours=time.hours, minutes=time.minutes, seconds=time.seconds, milliseconds=time.milliseconds)
		return time

	def round_time_up(self, time, freq):
		time = self.round_time_down(time, freq)
		return self.get_next_time(time, freq)