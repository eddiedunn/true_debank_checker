from sys import stderr
from loguru import logger
BLACK_COLOR = False # change to True if the table is displayed incorrectly
SLEEP_TIME = 0.5 # if you get a TOO MANY REQUESTS error, increase the sleep time between requests here
NODE_SLEEP_TIME = 0.1 # increase if your computer is a potato
FILE_JS = 'js/main.js'
FILE_EXCEL = 'DEBANK.xlsx'
FILE_WALLETS = 'wallets.txt'
DB_FILE = 'db/portfolio_history.db'
# LOGGING SETTING
FILE_LOG = 'logs/log.log'
logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - <white>{message}</white>")
logger.add(FILE_LOG, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - <white>{message}</white>")