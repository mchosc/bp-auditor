#!/usr/bin/env python3

import random
import logging
import trio
import json
import warnings
warnings.filterwarnings("ignore", category=trio.TrioDeprecationWarning)

from bp_auditor.queries import *
from bp_auditor.audit import *


url = 'https://telos.api.boid.animus.is'


async def test_check_one():
    chain_id = await get_chain_id(url)
    logging.info(f'{url} chain id {chain_id}')

    # Get top 42 producers ordered by vote
    producers = await get_all_producers(url)

    # Select a specific producer (e.g., the 16th) for detailed inspection
    selected_producer = producers[14]  # Using a fixed index for consistent debugging
    producer_report = await check_producer(url, selected_producer, chain_id)
    await check_all_producers(url, 10)
    # Log the JSON-formatted report
    logging.info(json.dumps(producer_report, indent=4))

    # Here you can use `producer_report` as a dictionary for further processing if needed
    # For example, print or analyze the raw data
    print("Raw producer report data:", producer_report)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    trio.run(test_check_one)