class Order:
	def __init__(self, symbol, amount, order_type, timeindex = None, price=None, stop_loss=None, take_profit=None, trailing_stop=None):
		self.timeindex = timeindex
		self.symbol = symbol
		self.order_type = order_type
		self.amount = amount
		self.open_price = price
		self.stop_loss = stop_loss
		self.take_profit = take_profit
		self.trailing_stop = trailing_stop

	def print_order(self):
		print "Order: Symbol=%s, Type=%s, amount=%s, Side=%s" % \
			  (self.symbol, self.order_type, self.amount, self.side)

class Trade:
	def __init__(self, order, open_price):
		self.timeindex = order.timeindex
		self.symbol = order.symbol
		self.amount = order.amount
		self.stop_loss = order.stop_loss
		self.take_profit = order.take_profit
		self.trailing_stop = order.trailing_stop
		self.open_price = open_price
		self.extreme_value = open_price

		self.bracketed = (self.take_profit != None and self.trailing_stop != None and self.stop_loss != None)

		self.close_price = None
		self.profit = None

	def print_Trade(self):
		print "Trade: Symbol=%s, Quantity=%s" % \
			  (self.symbol, self.quantity)