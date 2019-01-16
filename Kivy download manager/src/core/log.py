import logging
from datetime import datetime

def get_logger(name, level):
	frmt = logging.Formatter("[%(levelname)-8s] [%(asctime)s] [%(threadName)-12s] %(message)s")
	logfile = "data/log/{}.log".format(str(datetime.now()).replace(":","-"))
	logger = logging.getLogger(name)

	fhandler = logging.FileHandler(logfile, mode="w", encoding="utf-8")
	fhandler.setFormatter(frmt)
	logger.addHandler(fhandler)

	chandler = logging.StreamHandler()
	chandler.setFormatter(frmt)
	logger.addHandler(chandler)

	logger.setLevel(level)
	logger.info("<{}> created.".format(logfile))

	return logger