"""
This module provides various utility functions for handling questions.

It includes functions to:
- Retrieve the number of threads.
- Perform other question-related operations.

Functions:
- get_num_of_threads: Retrieves the number of threads based on specific criteria.
"""

import inquirer
from termcolor import colored
from inquirer.themes import load_theme_from_dict as loadth

from .config import *

def get_action():
    theme = {
        "Question": {
            "brackets_color": "bright_yellow"
        },
        "List": {
            "selection_color": "bright_blue"
        }
    }

    question = [
        inquirer.List(
            "action",
            message=colored("Select an action", 'light_yellow'),
            choices=["Get balances for all tokens in wallets", "Get balance for a specific token only", "Help", "Exit"],
        )
    ]
    action = inquirer.prompt(question, theme=loadth(theme))['action']
    return action

def select_chains(chains):
    theme = {
        "Question": {
            "brackets_color": "bright_yellow"
        },
        "List": {
            "selection_color": "bright_blue"
        }
    }

    question = [
        inquirer.Checkbox(
            "chains",
            message=colored("Select networks for which to get balances (check the required options using arrow keys <- ->)", 'light_yellow'),
            choices=["ALL NETWORKS", *chains],
        )
    ]
    selected_chains = inquirer.prompt(question, theme=loadth(theme))['chains']
    if ('ALL NETWORKS' in selected_chains):
        return chains
    return selected_chains

def get_ticker():
    theme = {
        "Question": {
            "brackets_color": "bright_yellow"
        },
        "List": {
            "selection_color": "bright_blue"
        }
    }

    question = [
        inquirer.Text("ticker", message=colored("Enter the name (ticker) of the token", 'light_yellow'))
    ]
    ticker = inquirer.prompt(question, theme=loadth(theme))['ticker'].upper()
    return ticker

def get_minimal_amount_in_usd():
    while True:
        theme = {
            "Question": {
                "brackets_color": "bright_yellow"
            },
            "List": {
                "selection_color": "bright_blue"
            }
        }

        question = [
                inquirer.Text("min_amount", message=colored("Enter the minimum amount in $ from which the token will be displayed in the table", 'light_yellow'), default="0.01")
        ]
        try:
            min_amount = float(inquirer.prompt(question, theme=loadth(theme))['min_amount'].strip())
            break
        except:
            logger.error('Error! Invalid input')
    if (min_amount) == 0:
        min_amount = -1
    return min_amount

def get_num_of_threads():
    while True:
        theme = {
            "Question": {
                "brackets_color": "bright_yellow"
            },
            "List": {
                "selection_color": "bright_blue"
            }
        }

        question = [
                inquirer.Text("num_of_threads", message=colored("Number of worker threads (if you have > 100 addresses, set only 1 thread)", 'light_yellow'), default="1")
        ]
        try:
            num_of_threads = int(inquirer.prompt(question, theme=loadth(theme))['num_of_threads'].strip())
            break
        except:
            logger.error('Error! Invalid input')
    if (num_of_threads) == 0:
        num_of_threads = 3
    return num_of_threads
