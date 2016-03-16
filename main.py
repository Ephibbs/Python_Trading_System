from data import *
from event import *
from execution import *
from portfolio import *
from strategy import *
from Queue import Queue

if __name__ == "__main__":
	start = "01-01-2002"
	end = "01-01-2002"


	bars = HistDataDotComDataHandler("data", start, end)
	broker = ForexBacktester(bars)
	strat = SMAC(bars)
	port = SimplePortfolio(bars, strat, broker)

	while True:
		if bars.continue_backtest:
			try:
				bars.update_bars()
			except:
				print "backtest over"
				break
		else:
			break

		broker.update()
		port.update()

		#generates and sends orders to broker
		port.trade()

	performance = port.performance