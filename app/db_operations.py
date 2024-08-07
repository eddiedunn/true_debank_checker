"""
This module contains functions for performing database operations related to the pool table.
It includes functions to insert data into the pool table, update existing records, and query
the database for specific information.

Functions:
- insert_pool_data: Inserts a new record into the pool table.
- update_pool_data: Updates an existing record in the pool table.
- get_pool_data: Retrieves data from the pool table based on specific criteria.
- delete_pool_data: Deletes a record from the pool table.
"""

import sqlite3
from contextlib import closing

def get_db_connection(db_file):
    """
    Establishes a connection to the SQLite database specified by db_file.

    Args:
        db_file (str): The path to the SQLite database file.

    Returns:
        sqlite3.Connection: A connection object to the SQLite database.
    """
    return sqlite3.connect(db_file)

def save_to_database(db_file, wallets, chains, coins, pools):
    """
    Saves wallet, chain, coin, and pool data to the specified SQLite database.

    Args:
        db_file (str): The path to the SQLite database file.
        wallets (list): A list of wallet data to be saved.
        chains (list): A list of chain data to be saved.
        coins (list): A list of coin data to be saved.
        pools (list): A list of pool data to be saved.

    Returns:
        None
    """
    print(f'inserting data to {db_file}')
    with closing(get_db_connection(db_file)) as conn:
        with conn:
            cursor = conn.cursor()

            # Create a new import run
            cursor.execute("INSERT INTO import_run DEFAULT VALUES")
            import_run_id = cursor.lastrowid
            print(f"Created new import run with ID: {import_run_id}")

            # Insert wallets
            cursor.executemany("INSERT OR IGNORE INTO wallet (address) VALUES (?)",
                               [(wallet,) for wallet in wallets])
            print(f"Inserted {len(wallets)} wallets")

            # Insert chains
            cursor.executemany("INSERT OR IGNORE INTO chain (name) VALUES (?)",
                               [(chain,) for chain in chains])
            print(f"Inserted {len(chains)} chains")

            # Prepare token lookup
            cursor.execute("SELECT id, name FROM token")
            token_lookup = {name: id for id, name in cursor.fetchall()}

            # Insert tokens and wallet_tokens

            wallet_token_count = 0
            for chain in coins:
                chain_id = cursor.execute("SELECT id FROM chain WHERE name = ?", (chain,)).fetchone()[0]
                for wallet, tokens in coins[chain].items():
                    wallet_id = cursor.execute("SELECT id FROM wallet WHERE address = ?", (wallet,)).fetchone()[0]
                    for token in tokens:
                        if token['name'] not in token_lookup:
                            cursor.execute("INSERT INTO token (name) VALUES (?)", (token['name'],))
                            token_lookup[token['name']] = cursor.lastrowid
                        token_id = token_lookup[token['name']]


                        cursor.execute(
                            """
                            INSERT INTO wallet_token (import_run_id, token_id, wallet_id, chain_id, quantity, token_price, value)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                import_run_id, token_id, wallet_id, chain_id,
                                token['amount'], token['price'], token['amount'] * token['price']
                            )
                        )
                        wallet_token_count += 1

            print(f"Inserted  {wallet_token_count} wallet_tokens")

            # Prepare protocol lookup
            cursor.execute("SELECT id, name FROM protocol")
            protocol_lookup = {name: id for id, name in cursor.fetchall()}

            # Insert protocols and pools
            protocol_count = 0
            pool_count = 0
            for pool_name, pool_data in pools.items():
                protocol_name, chain_name = pool_name.rsplit(' ', 1)
                chain_name = chain_name.strip('()')

                if protocol_name not in protocol_lookup:
                    cursor.execute("INSERT INTO protocol (name) VALUES (?)", (protocol_name,))
                    protocol_lookup[protocol_name] = cursor.lastrowid
                protocol_id = protocol_lookup[protocol_name]
                protocol_count += 1

                chain_id = cursor.execute("SELECT id FROM chain WHERE name = ?", (chain_name,)).fetchone()[0]

                for wallet, tokens in pool_data.items():
                    wallet_id = cursor.execute("SELECT id FROM wallet WHERE address = ?", (wallet,)).fetchone()[0]
                    for token in tokens:
                        if token['name'] not in token_lookup:
                            cursor.execute("INSERT INTO token (name) VALUES (?)", (token['name'],))
                            token_lookup[token['name']] = cursor.lastrowid
                        token_id = token_lookup[token['name']]

                        cursor.execute(
                            """
                            INSERT INTO pool (
                                import_run_id, token_id, wallet_id, chain_id, protocol_id, quantity, token_price, value
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                import_run_id, token_id, wallet_id, chain_id, protocol_id,
                                token['amount'], token['price'], token['amount'] * token['price']
                            )
                        )
                        pool_count += 1

    print(f"Inserted {protocol_count} protocols and {pool_count} pool entries to {db_file} database")