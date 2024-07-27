from loguru import logger
from sys import stderr
BLACK_COLOR = False # change to True if the table is displayed incorrectly
SLEEP_TIME = 0.5 # if you get a TOO MANY REQUESTS error, increase the sleep time between requests here
NODE_SLEEP_TIME = 0.1 # increase if your computer is a potato
file_js = 'js/main.js'
file_excel = 'DEBANK.xlsx'
file_wallets = 'wallets.txt'
# LOGGING SETTING
file_log = 'logs/log.log'
logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - <white>{message}</white>")
logger.add(file_log, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - <white>{message}</white>")