from data import *
from event import *
from execution import *
from strategy import *
from timer import *
from data import *
from portfolio import *
from performance import *


if __name__ == "__main__":
	start = None#"2016-3-10 00:00:00"
	#end = "2016-3-11 00:10:00"
	duration = "4H"
	start_balance = 1000000

	#initialize classes
	#broker = Oanda_Trader(clock, start_balance, slippage=0.0001)
	clock = Forex_Time_Manager(start=start, duration=duration, freq="1T")
	broker = Oanda_Trader(clock, start_balance)

	strat = SMAC(broker, freq="5T")
	perf = Performance(broker, freq="1T")
	port = SimplePortfolio(broker, strat, perf)

	port.sleepUntilNextTimeIndex()

	while port.iscontinue:

		port.trade()

		broker.update()
		if perf.ready():
			print clock.timeindex, ":  ", broker.portfolio_value
			perf.update()

		port.sleepUntilNextTimeIndex()

	broker.close_open_positions()

	#output results
	perf.plot_pnl()