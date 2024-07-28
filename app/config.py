"""
Configuration settings for the True Debank Checker application.

This module sets various configuration parameters and logging settings used throughout the application.

Attributes:
    BLACK_COLOR (bool): Flag to change table display color if displayed incorrectly.
    SLEEP_TIME (float): Time to sleep between requests to avoid TOO MANY REQUESTS errors.
    NODE_SLEEP_TIME (float): Time to sleep between node operations, adjust based on computer performance.
    FILE_JS (str): Path to the main JavaScript file.
    FILE_EXCEL (str): Path to the Excel file used for storing data.
    FILE_WALLETS (str): Path to the text file containing wallet addresses.
    DB_FILE (str): Path to the SQLite database file.
    FILE_LOG (str): Path to the log file.

Logging:
    Configures the loguru logger to log messages to both stderr and a log file with a specific format.
"""

from sys import stderr
from loguru import logger
BLACK_COLOR = False # change to True if the table is displayed incorrectly
SLEEP_TIME = 0.5 # if you get a TOO MANY REQUESTS error, increase the sleep time between requests here
NODE_SLEEP_TIME = 0.1 # increase if your computer is a potato
FILE_JS = 'js/main.js'
FILE_EXCEL = 'DEBANK.xlsx'
FILE_WALLETS = 'wallets.txt'
DB_FILE = 'db/portfolio_history.db'
SCHEMA_FILE = 'db/schema.sql'
# LOGGING SETTING
FILE_LOG = 'logs/log.log'
logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - <white>{message}</white>")
logger.add(FILE_LOG, format="<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <cyan>{line}</cyan> - <white>{message}</white>")
