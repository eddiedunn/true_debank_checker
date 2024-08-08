"""This module provides utilities for managing Node.js subprocesses and handling HTTP requests."""

import json
import random
import subprocess
from time import time, sleep

from loguru import logger
import tls_client

from app.config import NODE_SLEEP_TIME, SLEEP_TIME, FILE_JS

class NodeProcess:
    """
    Manages a Node.js subprocess for communication between Python and Node.js.

    This class handles starting, communicating with, and closing a Node.js subprocess.
    It provides methods for writing to and reading from the subprocess, and implements
    context manager protocol for safe resource management.
    """

    def __init__(self):
        self.process = None
        self._start_process()

    def _start_process(self):
        """
        Starts a new Node.js subprocess.

        If a process is already running, it closes the existing one before starting a new one.
        """
        logger.info("Starting Node.js process")
        if self.process:
            self.close()

        with subprocess.Popen(
            ['node', FILE_JS],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        ) as process:
            self.process = process
            logger.info("Node.js process started")

    def __enter__(self):
        """
        Enters the context manager protocol.

        Returns:
            NodeProcess: The instance itself.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exits the context manager protocol, ensuring the subprocess is closed.

        Args:
            exc_type: The exception type if an exception was raised.
            exc_val: The exception value if an exception was raised.
            exc_tb: The traceback if an exception was raised.
        """
        self.close()

    def write(self, data):
        """
        Writes data to the Node.js subprocess.

        Attempts to write data to the subprocess, retrying up to 3 times if an error occurs.

        Args:
            data: The data to write to the subprocess.

        Raises:
            RuntimeError: If writing fails after multiple attempts.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.process.stdin.write(data)
                self.process.stdin.flush()
                return
            except (ValueError, IOError) as e:
                logger.error(f"Error writing to Node.js process (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info("Restarting Node.js process")
                    self._start_process()
                else:
                    raise RuntimeError("Failed to write to Node.js process after multiple attempts") from e

    def readline(self):
        """
        Reads a line from the Node.js subprocess.

        If an error occurs while reading, it restarts the subprocess and tries again.

        Returns:
            str: The line read from the subprocess, stripped of whitespace.
        """
        try:
            return self.process.stdout.readline().strip()
        except (ValueError, IOError) as e:
            logger.error(f"Error reading from Node.js process: {e}")
            self._start_process()
            return self.process.stdout.readline().strip()

    def close(self):
        """
        Closes the Node.js subprocess.

        Terminates the subprocess if it's running and waits for it to finish.
        """
        if self.process:
            logger.info("Closing Node.js process")
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None

        @property
        def stdin(self):
            """
            Get the stdin stream of the Node.js subprocess.

            If the subprocess is not currently running, this method will start it
            before returning the stdin stream.

            Returns:
                io.TextIOWrapper: The stdin stream of the Node.js subprocess.
            """
            if not self.process:
                self._start_process()
            return self.process.stdin

        @property
        def stdout(self):
            """
            Get the stdout stream of the Node.js subprocess.

            If the subprocess is not currently running, this method will start it
            before returning the stdout stream.

            Returns:
                io.TextIOWrapper: The stdout stream of the Node.js subprocess.
            """
            if not self.process:
                self._start_process()
            return self.process.stdout

def generate_req_params(node_process, payload, method, path):
    """
    Generates request parameters by communicating with the Node.js process.

    Args:
        node_process (NodeProcess): The Node.js process to communicate with.
        payload (dict): The payload to send to the Node.js process.
        method (str): The HTTP method of the request.
        path (str): The path of the request.

    Returns:
        dict: A dictionary containing generated signature parameters.

    Raises:
        RuntimeError: If generation fails after multiple attempts.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            _json = json.dumps(payload)
            node_process.write(f'{_json}|{method}|{path}\n')
            sleep(NODE_SLEEP_TIME * 2)  # Increased sleep time
            output_data = node_process.readline()
            if not output_data:
                raise ValueError("Empty response from Node.js process")
            signature = json.loads(output_data)
            return signature
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Error in generate_req_params (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                logger.info("Retrying generate_req_params")
            else:
                raise RuntimeError("Failed to generate request parameters after multiple attempts") from e

    # This line will never be reached due to the raise statement in the loop.
    # However, to satisfy the linter, we can add a return statement here.
    return None

def edit_session_headers(node_process, session, payload, method, path):
    """
    Edits session headers with generated signatures and additional information.

    Args:
        node_process (NodeProcess): The Node.js process to use for generating signatures.
        session: The session object whose headers will be edited.
        payload (dict): The payload used to generate the signature.
        method (str): The HTTP method of the request.
        path (str): The path of the request.
    """
    sig = generate_req_params(node_process, payload, method, path)
    session.headers['x-api-nonce'] = sig['nonce']
    session.headers['x-api-sign'] = sig['signature']
    session.headers['x-api-ts'] = str(sig['ts'])

    abc = 'abcdef0123456789'
    r_id = ''.join(random.choices(abc, k=32))
    r_time = str(int(time()))
    info = {
        'random_at': r_time,
        'random_id': r_id,
        'user_addr': None
    }
    account = json.dumps(info)
    session.headers['account'] = account

def send_request(node_process, session, method, url, payload=None, params=None):
    """
    Sends an HTTP request and handles the response.

    This function attempts to send a request, handling various response scenarios
    including success, rate limiting, and errors. It will retry the request if necessary.

    Args:
        node_process (NodeProcess): The Node.js process to use for header updates.
        session: The session object to use for the request.
        method (str): The HTTP method of the request.
        url (str): The URL to send the request to.
        payload (dict, optional): The payload to send with the request. Defaults to None.
        params (dict, optional): The query parameters to send with the request. Defaults to None.

    Returns:
        Response or None: The response object if successful, None otherwise.
    """
    if payload is None:
        payload = {}
    if params is None:
        params = {}

    while True:
        try:
            resp = _make_request(session, method, url, payload, params)

            if resp.status_code == 200:
                return _handle_success(resp)
            if resp.status_code == 429:
                _handle_rate_limit(resp, session)
            else:
                _handle_error(resp, method, url, session, payload)

        except (tls_client.exceptions.TLSClientExeption, json.JSONDecodeError) as error:
            logger.error(f'Unexpected error while sending request to {url}: {error}')

        _update_headers(node_process, session, payload, params, method, url)
        sleep(1)

def _make_request(session, method, url, payload, params):
    """
    Makes an HTTP request using the provided session.

    Args:
        session: The session object to use for the request.
        method (str): The HTTP method of the request.
        url (str): The URL to send the request to.
        payload (dict): The payload to send with the request.
        params (dict): The query parameters to send with the request.

    Returns:
        Response: The response object from the request.
    """
    if method == 'GET':
        return session.execute_request(method=method, url=url)
    return session.request(method=method, url=url, json=payload, params=params)

def _handle_success(resp):
    """
    Handles a successful HTTP response.

    Args:
        resp: The response object to handle.

    Returns:
        Response or None: The response object if it contains data, None otherwise.
    """
    if 'data' in resp.text and resp.json():
        sleep(random.uniform(SLEEP_TIME, SLEEP_TIME+0.05))
        return resp
    logger.error(f'Request not include data | Response: {resp.text}')
    return None

def _handle_rate_limit(resp, session):
    """
    Handles a rate-limited HTTP response.

    Args:
        resp: The response object to handle.
        session: The session object used for the request.
    """
    if 'Too Many' in resp.text:
        logger.error(f"Too many requests | Headers: {session.headers['x-api-nonce']}")
        sleep(random.uniform(SLEEP_TIME, SLEEP_TIME+0.05))
    else:
        logger.error(f'Unknown request error | Response: {resp.text}')

def _handle_error(resp, method, url, session, payload):
    """
    Handles an error HTTP response.

    Args:
        resp: The response object to handle.
        method (str): The HTTP method of the request.
        url (str): The URL of the request.
        session: The session object used for the request.
        payload (dict): The payload sent with the request.
    """
    logger.error(
        f'Bad request status code: {resp.status_code} | Method: {method} | Response: {resp.text} | Url: {url} | '
        f'Headers: {session.headers} | Payload: {payload}'
    )

def _update_headers(node_process, session, payload, params, method, url):
    """
    Updates the session headers for a new request.

    Args:
        node_process (NodeProcess): The Node.js process to use for generating signatures.
        session: The session object whose headers will be updated.
        payload (dict): The payload for the request.
        params (dict): The query parameters for the request.
        method (str): The HTTP method of the request.
        url (str): The URL of the request.
    """
    if method == 'GET':
        edit_session_headers(node_process, session, params, method, url.split('api.debank.com')[1].split('?')[0])
    else:
        edit_session_headers(node_process, session, payload, method, url)

def setup_session():
    """
    Sets up a session with appropriate headers and creates a Node.js process.

    Returns:
        tuple: A tuple containing the set up session and the created NodeProcess object.
    """
    session = tls_client.Session(
        client_identifier="chrome112",
        random_tls_extension_order=True
    )

    headers = {
        'authority': 'api.debank.com',
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9',
        'cache-control': 'no-cache',
        'origin': 'https://debank.com',
        'pragma': 'no-cache',
        'referer': 'https://debank.com/',
        'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'source': 'web',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'x-api-nonce': 'n_RT2KhwQF08JA3CwiTUOhUnel9ELZPGHDb2UgZLKh',
        'x-api-sign': 'fb69dcdb900a27540c6fd9e13a08db75d16a2b917cfc33991e834552691a1a72',
        'x-api-ts': '1690894427',
        'x-api-ver': 'v2',
    }
    session.headers = headers

    node_process = NodeProcess()
    return session, node_process
