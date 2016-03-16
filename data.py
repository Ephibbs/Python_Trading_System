import datetime
import pandas as pd
import json
import requests as r
import os
from oanda import *

from abc import ABCMeta, abstractmethod

class DataHandler(object):
	__metaclass__ = ABCMeta

	@abstractmethod
	def get_prices(self, symbol, N=1):
		raise NotImplementedError("Implement history()")

	@abstractmethod
	def update(self):
		raise NotImplementedError("Implement update_data()")

class Oanda_Data_Manager(DataHandler):
	def __init__(self, clock, use_local_data=True):
		self.clock = clock
		self.dataconn = Oanda()
		self.use_local_data = use_local_data #set to false for more realistic run time

		#Data Functions
	def get_prices(self, sym, freq="1T", count=1):
		now = self.clock.timeindex
		dir = "../data/oanda_data/%s" % sym
		fname = "%s/%s.pkl" % (dir, freq)
		#should we try to use local data?
		if self.use_local_data:
			#if no file, create one with oanda data
			if os.path.isfile(fname):
				allprices = pd.read_pickle(fname)
				lastnprices = allprices.loc[:now].iloc[-count:]
				time_range = pd.date_range(end=now, periods=count, freq=freq)
				#if not complete, fill in with oanda data, save new file and return data
				if not all(lastnprices.index == time_range):
					lastnprices = self.dataconn.get_prices(sym, end=self.clock.timeindex, freq=freq, count=count)
					allprices = allprices.combine_first(lastnprices)
					allprices.to_pickle(fname)
			else:
				lastnprices = self.dataconn.get_prices(sym, end=self.clock.timeindex, freq=freq, count=count)
				if not os.path.exists(dir):
					os.makedirs(dir)
				lastnprices.to_pickle(fname)
		else:
				lastnprices = self.dataconn.get_prices(sym, end=self.clock.timeindex, freq=freq, count=count)
		return lastnprices

	def get_current_price(self, sym):
		return self.get_prices(sym, freq="5S")

	def update(self):
		pass