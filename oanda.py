import requests as r
import json
import pandas as pd

class Oanda:
	def __init__(self, access_token='7e7d4458f14b85286e4a2df19d09a996-7b8754093cf8f1f5bf51357a47e5a071',
				 account_id = '8212557', type='practice', verbose=True):

		self.ENV = {
			"streaming": {
				"real": "stream-fxtrade.oanda.com",
				"practice": "stream-fxpractice.oanda.com",
				"sandbox": "stream-sandbox.oanda.com"
			},
			"api": {
				"real": "api-fxtrade.oanda.com",
				"practice": "api-fxpractice.oanda.com",
				"sandbox": "api-sandbox.oanda.com"
			}
		}

		base_url = "https://" + self.ENV["api"][type]
		self.account_url = base_url + "/v1/accounts/" + account_id
		self.order_url = self.account_url + "/orders"
		self.trade_url = self.account_url + "/trades"
		self.positions_url = self.account_url + "/positions"
		self.candles_url = base_url + "/v1/candles"
		self.transaction_url = base_url + "/v1/transactions"

		self.headers = {'Authorization' : 'Bearer ' + access_token,
						 'Connection' : 'Keep-Alive',
						#'Accept-Encoding': 'gzip, deflate'
						#'X-Accept-Datetime-Format' : 'unix'
						  }
		self.verbose = verbose

	#orders

	def send_order(self, order):
		#load parameters
		paramst = {}
		paramst["instrument"] = order.symbol
		paramst["units"] = order.amount
		paramst["side"] = order.side
		if order.type == None:
			paramst["type"] = "market"
		if paramst["trailingStop"] != None:
			paramst["trailingStop"] = order.trailing_stop

		req = r.post(self.candles_url, headers = self.headers, data= paramst)
		resp = json.loads(req.text)

		return resp

	def send_order(self, sym, amount, trailing_stop=None, type=None):
		#load parameters
		paramst = {}
		paramst["instrument"] = sym
		paramst["units"] = abs(amount)
		paramst["side"] = "buy" if amount > 0 else "sell"
		if type == None:
			paramst["type"] = "market"
		else:
			paramst["type"] = type
		if trailing_stop != None:
			paramst["trailingStop"] = trailing_stop

		req = r.post(self.order_url, headers = self.headers, data= paramst)
		resp = json.loads(req.text)

		return resp

	def close_order(self, order_or_orderid):
		url_end = order_or_orderid if type(order_or_orderid) == str else order_or_orderid.order_id
		url = self.order_url + "/" + url_end
		req = r.delete(url, headers = self.headers)
		resp = json.loads(req.text)
		return resp

	def get_positions(self):
		req = r.get(self.positions_url, headers = self.headers)
		resp = json.loads(req.text)['positions']
		return resp

	def get_transaction_history(self):
		url = self.account_url + "/transactions"
		req = r.get(url, headers = self.headers)
		resp = json.loads(req.text)['transactions']
		return resp

	def get_last_transaction_id(self):
		hist = self.get_transaction_history()
		return hist[0]["id"]+1

	def close_open_position(self, sym):
		url = self.positions_url + "/" + sym
		req = r.delete(url, headers = self.headers)
		resp = json.loads(req.text)
		return resp

	'''
	def close_out_everything(self):
		req = r.get(self.order_url, headers = self.headers)
		all_orders = json.loads(req.text)

		req = r.get(self.order_url, headers = self.headers)
		all_orders = json.loads(req.text)

		url = self.candles_url + url_end
		req = r.delete(url, headers = self.headers)
		json1_data = json.loads(req.text)

		return json1_data
	'''

	#data
	def get_prices(self, symbol, count=None, freq="15T", start=None, end=None, candleFormat=None):

		freq = self.freq_format_converter(freq)

		#load parameters
		paramst = {}
		paramst["instrument"] = symbol
		if count != None:
			paramst["count"] = count
		paramst["granularity"] = freq
		if start != None:
			paramst["start"] = start.isoformat()
		if end != None:
			paramst["end"] = end.isoformat()
		if candleFormat != None:
			paramst["candleFormat"] = candleFormat

		req = r.get(self.candles_url, headers = self.headers, params = paramst)
		if self.verbose:
			print json.loads(req.text)
		json1_data = json.loads(req.text)
		df = pd.DataFrame(json1_data["candles"])
		df["time"] = pd.to_datetime(df["time"])
		return df.set_index("time")

	def freq_format_converter(self, freq):
		if freq[0].isalpha(): #from oanda
			step = freq[0]
			num = freq[1:]
			step = step.replace("M","T")
			return num+step
		else:				 #from pandas
			step = freq[-1]
			num = freq[:-1]
			step = step.replace("T","M")
			return step+num

	def get_account_data(self):
		req = r.get(self.account_url, headers = self.headers)
		json1_data = json.loads(req.text)
		return json1_data

