import numpy as np
import pandas as pd

from abc import ABCMeta, abstractmethod

class Strategy(object):
	__metaclass__ = ABCMeta

	@abstractmethod
	def trade(self):
		raise NotImplementedError("Should implement calculate_signals()")

class SMAC(Strategy):
	def __init__(self, broker, freq="1T"):
		self.broker = broker
		self.parameters = {"slow_window_size": 25, "fast_window_size": 3, "buffer": 0.0005}
		self.freq = freq

	def trade(self):
		slow_window = self.parameters["slow_window_size"]
		fast_window = self.parameters["fast_window_size"]
		open_bars = self.broker.get_prices("EUR_USD", count=slow_window)["openBid"]
		slow = pd.rolling_mean(open_bars, slow_window).iloc[-1]
		fast = pd.rolling_mean(open_bars, fast_window).iloc[-1]
		buf = self.parameters["buffer"]
		if fast - slow > buf:
			self.broker.order_target("EUR_USD", 10000, trail_stop=5)
		elif slow - fast > buf:
			self.broker.order_target("EUR_USD", -10000, trail_stop=5)


class BB_Reversal(Strategy):
	def __init__(self, bars, broker, clock):
		self.bars = bars
		self.broker = broker
		self.clock = clock
		self.parameters = {"slow_window_size": 25, "fast_window_size": 3}
		self.timeindex = None
		self.freq = "15T"
