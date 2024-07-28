#!/usr/bin/env python3
"""
This script initializes and runs the main application for checking blockchain balances and generating reports.
"""

import argparse
import sys
import threading
from queue import Queue
from time import time

from termcolor import colored
from art import text2art
from alive_progress import alive_bar

from app.excel import save_full_to_excel, save_selected_to_excel
from app.questions import (
    get_minimal_amount_in_usd, get_num_of_threads,
    select_chains, get_action, get_ticker
)
from app.config import DB_FILE, FILE_EXCEL, FILE_WALLETS
from app.utils import edit_session_headers, send_request, setup_session, logger
from app.db_operations import save_to_database

# ... (rest of the imports and functions remain the same)

def get_pools(node_process, session, wallets):
    """Get the pools information for all wallets."""
    def get_pool(session, address):
        pools = {}
        payload = {
            'user_addr': address,
        }
        edit_session_headers(node_process, session, payload, 'GET', '/portfolio/project_list')

        resp = send_request(
            node_process,
            session=session,
            method='GET',
            url=f'https://api.debank.com/portfolio/project_list?user_addr={address}',
        )

        for pool in resp.json()['data']:
            pools[f"{pool['name']} ({pool['chain']})"] = []
            for item in pool['portfolio_item_list']:
                for coin in item['asset_token_list']:
                    pools[f"{pool['name']} ({pool['chain']})"].append({
                        'amount': coin['amount'],
                        'name': coin['name'],
                        'ticker': coin['optimized_symbol'],
                        'price': coin['price'],
                        'logo_url': coin['logo_url']
                    })

        return pools
    
    all_pools = {}

    with alive_bar(len(wallets)) as progress_bar:
        for wallet in wallets:
            pools = get_pool(session, wallet)
            for pool_name, pool_data in pools.items():
                if pool_name not in all_pools:
                    all_pools[pool_name] = {}
                all_pools[pool_name][wallet] = pool_data
            progress_bar()()

    for pool in all_pools:
        for wallet in wallets:
            if wallet not in all_pools[pool]:
                all_pools[pool][wallet] = []
    print()

    return all_pools

def process_balances(wallets, selected_chains, ticker, min_amount, num_of_threads):
    """Process balances for all wallets."""
    coins = {chain: {} for chain in selected_chains}
    pools_names = list(pools)
    
    queue_tasks = Queue()
    queue_results = Queue()

    threads = []
    for _ in range(num_of_threads):
        th = threading.Thread(target=worker, args=(queue_tasks, queue_results))
        threads.append(th)
        th.start()

    start_time = time()
    for chain_id, chain in enumerate(selected_chains):
        if chain not in pools_names:
            logger.info(f'[{chain_id + 1}/{len(selected_chains) - len(set(selected_chains) & set(pools_names))}] '
                        f'Getting balance in network {chain.upper()}...')

            for wallet in wallets:
                queue_tasks.put(('chain_balance', wallet, chain, ticker, min_amount))

            with alive_bar(len(wallets)) as progress_bar:
                for _ in wallets:
                    result = queue_results.get()
                    coins[result[0]][result[1]] = result[2]
                    progress_bar()()

    print()
    logger.info('Getting balance in all networks for each wallet')
    for wallet in wallets:
        queue_tasks.put(('get_wallet_balance', wallet))

    balances = {}
    with alive_bar(len(wallets)) as progress_bar:
        for _ in wallets:
            result = queue_results.get()
            balances[result[0]] = result[1]
            progress_bar()()

    queue_tasks.put(('done',))
    for th in threads:
        th.join()

    return coins, balances

def get_balances(wallets, ticker=None, auto_import=False):
    """Get balances for all wallets."""
    session, node_process = setup_session()

    logger.info('Getting list of networks used on wallets...')
    chains = list(get_chains(node_process, session, wallets))
    logger.info('Getting list of pools and wallet balances in them...')
    pools = get_pools(node_process, session, wallets)
    logger.success(f'Done! Total networks and pools: {len(chains) + len(pools)}\n')

    if auto_import:
        min_amount = 7
        selected_chains = chains + list(pools)
        num_of_threads = 1
    else:
        min_amount = get_minimal_amount_in_usd()
        selected_chains = select_chains(chains + list(pools))
        num_of_threads = get_num_of_threads()

    coins, balances = process_balances(wallets, selected_chains, ticker, min_amount, num_of_threads)

    # Save output
    if auto_import:
        save_to_database(DB_FILE, wallets, selected_chains, coins, pools)
        logger.success('Done! Data saved to database')
    else:
        if ticker is None:
            save_full_to_excel(wallets, selected_chains, coins, balances)
        else:
            save_selected_to_excel(wallets, selected_chains, coins, balances, ticker)
        print()
        logger.success(f'Done! Table saved in {FILE_EXCEL}')

    logger.info(f'Time taken: {round((time() - start_time) / 60, 1)} min.\n')

def main():
    """Main function to run the application."""
    art = text2art(text="DEBANK   CHECKER", font="standart")
    print(colored(art, 'light_blue'))
    print(colored('Author: t.me/cryptogovnozavod\n', 'light_cyan'))

    with open(FILE_WALLETS, 'r', encoding='utf-8') as file:
        wallets = [row.strip().lower() for row in file]

    logger.success(f'Successfully loaded {len(wallets)} addresses\n')

    parser = argparse.ArgumentParser()
    parser.add_argument('--auto-import', action='store_true', help='Run automatic import on all chains')
    args = parser.parse_args()

    if args.auto_import:
        get_balances(wallets, auto_import=True)
    else:
        while True:
            action = get_action()

            if action == 'Get balances for all tokens in wallets':
                get_balances(wallets)
            elif action == 'Get balance for a specific token only':
                ticker = get_ticker()
                get_balances(wallets, ticker)
            elif action == 'Help':
                show_help()
            elif action == 'Exit':
                sys.exit()

if __name__ == '__main__':
    main()