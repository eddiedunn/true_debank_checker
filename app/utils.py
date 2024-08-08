"""This module provides utilities for managing Node.js subprocesses and handling HTTP requests."""

import json
import random
import subprocess
from time import time, sleep

from loguru import logger
import tls_client

from app.config import NODE_SLEEP_TIME, SLEEP_TIME, FILE_JS

class NodeProcess:
    """Manages a Node.js subprocess for generating request parameters and signatures."""

    def __init__(self):
        self.process = None
        self._start_process()

    def _start_process(self):
        """Start the Node.js subprocess if it's not running."""
        if not self.process or self.process.poll() is not None:
            with subprocess.Popen(
                ['node', FILE_JS],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                universal_newlines=True
            ) as process:
                self.process = process

    def __enter__(self):
        """Enter the context manager."""
        self._start_process()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and close the process."""
        self.close()

    def close(self):
        """Terminate the subprocess."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    @property
    def stdin(self):
        """Get the stdin of the subprocess."""
        self._start_process()
        return self.process.stdin

    @property
    def stdout(self):
        """Get the stdout of the subprocess."""
        self._start_process()
        return self.process.stdout

    def write(self, data):
        """Write data to the subprocess stdin."""
        self.stdin.write(data)
        self.stdin.flush()

    def readline(self):
        """Read a line from the subprocess stdout."""
        return self.stdout.readline()

def generate_req_params(node_process, payload, method, path):
    """Generate request parameters and signatures using a subprocess."""
    _json = json.dumps(payload)

    node_process.write(f'{_json}|{method}|{path}\n')
    sleep(NODE_SLEEP_TIME)
    output_data = node_process.readline().strip()
    signature = json.loads(output_data)

    return signature

def edit_session_headers(node_process, session, payload, method, path):
    """Edit session headers with generated signatures."""
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
    """Send an HTTP request using the provided session and handle the response."""
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
    if method == 'GET':
        return session.execute_request(method=method, url=url)
    return session.request(method=method, url=url, json=payload, params=params)

def _handle_success(resp):
    if 'data' in resp.text and resp.json():
        sleep(random.uniform(SLEEP_TIME, SLEEP_TIME+0.05))
        return resp
    logger.error(f'Request not include data | Response: {resp.text}')
    return None

def _handle_rate_limit(resp, session):
    if 'Too Many' in resp.text:
        logger.error(f"Too many requests | Headers: {session.headers['x-api-nonce']}")
        sleep(random.uniform(SLEEP_TIME, SLEEP_TIME+0.05))
    else:
        logger.error(f'Unknown request error | Response: {resp.text}')

def _handle_error(resp, method, url, session, payload):
    logger.error(
        f'Bad request status code: {resp.status_code} | Method: {method} | Response: {resp.text} | Url: {url} | '
        f'Headers: {session.headers} | Payload: {payload}'
    )

def _update_headers(node_process, session, payload, params, method, url):
    if method == 'GET':
        edit_session_headers(node_process, session, params, method, url.split('api.debank.com')[1].split('?')[0])
    else:
        edit_session_headers(node_process, session, payload, method, url)

def setup_session():
    """Set up a session with appropriate headers and create a node process."""
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

    return session, NodeProcess()
