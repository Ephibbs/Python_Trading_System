import datetime
import numpy as np
import pandas as pd
import Queue

from abc import ABCMeta, abstractmethod
from math import floor

class Portfolio(object):

	__metaclass__ = ABCMeta

	@abstractmethod
	def trade(self, signals):
		raise NotImplementedError("Should implement trade()")


class SimplePortfolio(Portfolio):
	def __init__(self, broker, strategy, perf):
		self.broker = broker
		self.clock = broker.clock
		self.perf = perf
		self.strategy = strategy
		self.iscontinue = self.clock.iscontinue

		self.strategy_trade_time = self.clock.get_next_time(strategy.freq)

	def trade(self):
		self.update()
		if self.clock.now() > self.strategy_trade_time:
			self.strategy.trade()
			self.strategy_trade_time = self.clock.get_next_time(self.strategy.freq)

	def update(self):
		#if self.perf.curr_drawdown() > self.max_DD:
		#	self.stop()
		self.iscontinue = self.clock.iscontinue


	def sleepUntilNextTimeIndex(self):
		self.clock.sleepUntilNextTimeIndex()
