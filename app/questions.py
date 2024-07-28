"""
This module provides various utility functions for handling questions.

It includes functions to:
- Retrieve user actions
- Select chains
- Get token tickers
- Set minimal amounts
- Get the number of threads
"""

import logging
from typing import List

import inquirer
from termcolor import colored
from inquirer.themes import load_theme_from_dict as loadth

logger = logging.getLogger(__name__)

THEME = {
    "Question": {
        "brackets_color": "bright_yellow"
    },
    "List": {
        "selection_color": "bright_blue"
    }
}

def get_action() -> str:
    """Prompt the user to select an action."""
    question = [
        inquirer.List(
            "action",
            message=colored("Select an action", 'light_yellow'),
            choices=[
                "Get balances for all tokens in wallets",
                "Get balance for a specific token only",
                "Help",
                "Exit"
            ],
        )
    ]
    action = inquirer.prompt(question, theme=loadth(THEME))['action']
    return action

def select_chains(chains: List[str]) -> List[str]:
    """Prompt the user to select chains."""
    question = [
        inquirer.Checkbox(
            "chains",
            message=colored(
                "Select networks for which to get balances "
                "(check the required options using arrow keys <- ->)",
                'light_yellow'
            ),
            choices=["ALL NETWORKS", *chains],
        )
    ]
    selected_chains = inquirer.prompt(question, theme=loadth(THEME))['chains']
    return chains if 'ALL NETWORKS' in selected_chains else selected_chains

def get_ticker() -> str:
    """Prompt the user to enter a token ticker."""
    question = [
        inquirer.Text("ticker", message=colored("Enter the name (ticker) of the token", 'light_yellow'))
    ]
    ticker = inquirer.prompt(question, theme=loadth(THEME))['ticker'].upper()
    return ticker

def get_minimal_amount_in_usd() -> float:
    """Prompt the user to enter a minimum amount in USD."""
    while True:
        question = [
            inquirer.Text("min_amount", message=colored("Enter the minimum amount in $ from which the token will be displayed in the table", 'light_yellow'), default="0.01")
        ]
        try:
            min_amount = float(inquirer.prompt(question, theme=loadth(THEME))['min_amount'].strip())
            return -1 if min_amount == 0 else min_amount
        except ValueError:
            logger.error('Error! Invalid input')

def get_num_of_threads() -> int:
    """Prompt the user to enter the number of worker threads."""
    while True:
        question = [
            inquirer.Text(
                "num_of_threads",
                message=colored(
                    "Number of worker threads (if you have > 100 addresses, set only 1 thread)",
                    'light_yellow'
                ),
                default="1"
            )
        ]
        try:
            num_of_threads = int(
                inquirer.prompt(question, theme=loadth(THEME))['num_of_threads'].strip()
            )
            return 3 if num_of_threads == 0 else num_of_threads
        except ValueError:
            logger.error('Error! Invalid input')
