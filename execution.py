import pandas
import datetime
import Queue
from oanda import *
import numpy as np
import os

from event import *
from abc import ABCMeta, abstractmethod




class ExecutionManager(object):
	__metaclass__ = ABCMeta

	@abstractmethod
	def submit_order(self, symbol, amount, type="MARKET"):
		raise NotImplementedError("Should implement execute_order()")

	#@abstractmethod
	#def get_order_info(self, orderid):
	#	raise NotImplementedError("Should implement execute_order()")


class Oanda_Trader(ExecutionManager):
	#done in the style of Oanda
	def __init__(self, clock, start_balance, type="practice"):
		self.brokerconn = Oanda(type="practice")
		self.clock = clock

		#constants
		self.start_balance = self.brokerconn.get_account_data()["balance"]

		#reference for performance class
		self.portfolio_value = self.start_balance
		self.lasttransactionid = self.brokerconn.get_last_transaction_id()
		self.start_realizedPl = self.brokerconn.get_account_data()["realizedPl"]
		self.unrealizedPl = 0
		self.realizedPl = 0
		self.commnslip = 0
		self.closed_trades = []
		self.use_local_data = False

	def make_signed_units(self, units, side):
		return units if side == "buy" else -units

	def get_positions(self):
		return {e["instrument"]:self.make_signed_units(e["units"], e["side"]) for e in self.brokerconn.get_positions()}

	def submit_order(self, sym, amount, trail_stop):
		a = self.brokerconn.send_order(sym, amount, trail_stop)
		return a

	def order_target(self, sym, target, trail_stop=None):
		amount = target - self.get_positions().get(sym, 0)
		if amount != 0:
			self.submit_order(sym, amount, trail_stop)

	def get_account_info(self):
		account_info = self.brokerconn.get_account_data()
		positions = {e["instrument"]:e["units"] for e in self.brokerconn.get_positions()}
		self.portfolio_value = account_info["balance"] + account_info["unrealizedPl"]
		return {'balance': account_info["balance"],
				'portfolio_value': self.portfolio_value,
				'unrealizedPl': account_info["unrealizedPl"],
				'realizedPl': account_info["realizedPl"] - self.start_realizedPl,
				'PnL': self.portfolio_value - self.start_balance,
				'positions': positions,
				'commission': self.commnslip,
				}

	def close_open_positions(self):
		symbols = self.get_positions().keys()
		for sym in symbols:
			self.brokerconn.close_open_position(sym)

	def update(self):
		pass












class Oanda_Trader(ExecutionManager):
	#done in the style of Oanda
	def __init__(self, clock, start_balance, slippage, use_local_data=True):
		self.dataconn = Oanda()
		self.clock = clock

		#constants
		self.slippage = slippage
		self.start_balance = start_balance
		self.use_local_data = use_local_data

		#reference for performance class
		self.balance = self.start_balance
		self.portfolio_value = self.start_balance
		self.unrealizedPl = 0
		self.realizedPl = 0
		self.commission_sum = 0
		self.positions = {}
		self.trades = []
		self.closed_trades = []


	def _check_open_trades(self):
			trades = list(self.trades)
			for i in range(len(trades)):
				trade = trades[i]
				trade_closed = False
				if trade.bracketed:
					curr_price = self.get_current_price(trade.symbol)
					if trade.amount > 0:
						if curr_price["highBid"] > trade.take_profit:
							price = trade.take_profit-self.slippage
							self._execute_close_trade(trade, price)
							trade_closed = True
						elif curr_price["lowBid"] < trade.trailing_stop:
							price = max(curr_price["lowBid"], trade.trailing_stop-self.slippage)
							self._execute_close_trade(trade, price)
							trade_closed = True
						elif curr_price["lowBid"] < trade.stop_loss:
							price = max(curr_price["lowBid"], trade.stop_loss-self.slippage)
							self._execute_close_trade(trade, price)
							trade_closed = True
						elif curr_price["highBid"] > trade.extreme_value:
							trade.extreme_value = float(price["high"])
					else:
						if curr_price["lowAsk"] < trade.take_profit:
							price = trade.take_profit+self.slippage
							self._execute_close_trade(trade, price)
							trade_closed = True
						elif price["highAsk"] > trade.trailing_stop:
							price = min(curr_price["highAsk"], trade.trailing_stop+self.slippage)
							self._execute_close_trade(trade, price)
							trade_closed = True
						elif price["highAsk"] > trade.stop_loss:
							price = min(curr_price["highAsk"], trade.stop_loss+self.slippage)
							self._execute_close_trade(trade, price)
							trade_closed = True
						elif price["lowAsk"] < trade.extreme_value:
							trade.extreme_value = float(price["low"])
					if trade_closed:
						del self.trades[i]
						self.closed_trades.append(trade)

	def _execute_close_trade(self, trade, price):
		side = 2*(trade.amount > 0) - 1
		prevposition = self.positions.get(trade.symbol, 0)
		ordercost = float(price*trade.amount)

		trade.close_price = price
		trade.profit = side * (trade.close_price - trade.open_price)*trade.amount

		self.balance += trade.profit
		self.positions[trade.symbol] = float(prevposition - side * trade.amount)

		return trade

	def _get_unrealized_Pnl(self):
		unrealized_Pnl = 0
		for trade in self.trades:
			sym = trade.symbol
			open_price = trade.open_price
			pos = trade.amount
			if pos < 0:
				ask = self.get_current_price(sym)["openAsk"]
				unrealized_Pnl += (open_price - ask)*pos
			else:
				bid = self.get_current_price(sym)["openBid"]
				unrealized_Pnl += (bid - open_price)*pos
		return unrealized_Pnl


	def submit_order(self, sym, amount, type="MARKET"):
		order = Order(sym, amount, type)
		ask = self.get_current_price(order.symbol)["openAsk"] + self.slippage
		bid = self.get_current_price(order.symbol)["openBid"] - self.slippage
		prevposition = self.positions.get(order.symbol, 0)

		if order.amount > 0:
			price = ask
			ordercost = float(price*order.amount)
			self.positions[order.symbol] = float(prevposition + order.amount)
		else:
			price = bid
			ordercost = float(price*order.amount)
			self.positions[order.symbol] = float(prevposition - order.amount)

		self.commission_sum += float(ask) - float(bid)

		self.trades.append(Trade(order, open_price = price))

	def order_target(self, sym, target):
		amount = target - self.positions.get(sym, 0)
		self.submit_order(sym, amount)

	def get_account_info(self):
		closed_trades = list(self.closed_trades)
		self.closed_trades = []
		return {'balance': self.balance,
				'unrealizedPl': self.unrealizedPl,
				'realizedPl': self.realizedPl,
				'PnL': self.realizedPl + self.unrealizedPl,
				'positions': self.positions,
				'portfolio_value': self.portfolio_value,
				'commission': self.commission_sum,
				'closed_trades': closed_trades
				}

	def update(self):
		#update money measures
		self.unrealizedPl = self._get_unrealized_Pnl()
		self.realizedPl = float(self.balance - self.start_balance)
		self.portfolio_value = self.unrealizedPl + self.realizedPl + self.start_balance

		#check for trade closes
		self._check_open_trades()

	def close_open_positions(self):
		pass

	def close_all_trades(self, sym=None):
		trades = list(self.trades)
		for i in range(len(trades)):
			trade = trades[i]
			if trade.symbol == sym or sym == None:
				sym = trade.symbol
				amount = trade.amount
				curr_price = self.get_current_price(sym)
				if amount > 0:
					#sell
					price = curr_price["openBid"]-self.slippage
					trade = self._execute_close_trade(trade, price)
				else:
					#sell
					price = curr_price["openAsk"]+self.slippage
					trade = self._execute_close_trade(trade, price)
				del self.trades[i]
				self.closed_trades.append(trade)

	#Data Functions
	def get_prices(self, sym, freq="1T", count=1):
		now = self.clock.timeindex
		dir = "../data/oanda_data/%s" % sym
		fname = "%s/%s.pkl" % (dir, freq)
		#should we try to use local data?
		if self.use_local_data and not self.clock.islive:
			#if no file, create one with oanda data
			if os.path.isfile(fname):
				allprices = pd.read_pickle(fname)
				lastnprices = allprices.loc[:now].iloc[-count:]
				time_range = pd.date_range(end=now, periods=count, freq=freq)
				#if not complete, fill in with oanda data, save new file and return data
				if not all(lastnprices.index == time_range):
					lastnprices = self.dataconn.get_prices(sym, end=self.clock.now(), freq=freq, count=count)
					allprices = allprices.combine_first(lastnprices)
					allprices.to_pickle(fname)
			else:
				lastnprices = self.dataconn.get_prices(sym, end=self.clock.now(), freq=freq, count=count)
				if not os.path.exists(dir):
					os.makedirs(dir)
				lastnprices.to_pickle(fname)
		else:
				lastnprices = self.dataconn.get_prices(sym, end=self.clock.now(), freq=freq, count=count)
		return lastnprices

	def get_current_price(self, sym):
		return self.get_prices(sym, freq="5S", count=1).iloc[0]