import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.rcParams["axes.formatter.useoffset"] = False


class Performance:

	def __init__(self, broker, freq="D"):
		self.freq = freq
		self.broker = broker
		self.clock = broker.clock

		self.all_positions = pd.DataFrame(0, columns=[0], index=[self.clock.timeindex])
		self.all_holdings = self.construct_all_holdings()

		self.next_update_time = self.clock.get_next_time(freq)

	def construct_all_holdings(self):
		"""
        Constructs the holdings list using the start_date
        to determine when the time index will begin.
        """
		holding_columns = ['balance', 'portfolio_value', 'PnL', 'commission']
		all_holdings = pd.DataFrame([[self.broker.start_balance, self.broker.start_balance, 0, 0]], columns=holding_columns, index=[self.clock.timeindex])
		return all_holdings


	def update(self):
		account_info = self.broker.get_account_info()
		self.update_positions(account_info["positions"])
		self.all_holdings.loc[self.clock.timeindex] = [account_info['balance'], account_info['portfolio_value'], account_info['PnL'], account_info['commission']]

		self.next_update_time = self.clock.get_next_time(self.freq)

	def update_positions(self, positions):
		if len(positions.keys()) > 0:
			self.all_positions.loc[self.clock.timeindex] = 0
			for sym,pos in positions.items():
				if not sym in self.all_positions.columns:
					pos_series = pd.DataFrame(0, index=self.all_positions.index, columns=[sym])
					self.all_positions = pd.concat([self.all_positions, pos_series])
				self.all_positions[sym].loc[self.clock.timeindex] = pos

	def plot_pnl(self):
		self.all_holdings["PnL"].plot()
		plt.show()

	def plot_returns(self):
		returns = self.all_holdings["PnL"]/self.all_holdings['balance'].iloc[0]
		returns.plot()
		plt.show()

	def plot_portfolio_value(self):
		portfolio_values = self.all_holdings["portfolio_value"]
		portfolio_values.plot()
		plt.show()

	def ready(self):
		return self.clock.now() > self.next_update_time