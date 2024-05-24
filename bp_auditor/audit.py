#!/usr/bin/env python3

import logging

import trio

from .queries import *

async def check_producer(chain_url: str, producer: dict, chain_id: str):
    report = {
        'owner': producer.get('owner', 'Unknown'),
        'url': producer.get('url', 'No URL available'),
        'bp_json': 'Not attempted',
        'ssl_endpoints': [],
        'p2p_endpoints': [],
        'history': {
            'HTTP': "Not attempted",
            'HTTPS': "Not attempted"
        },
        'cpu': 'Not attempted'
    }
    url = producer['url']

    if not url:
        report['bp_json'] = 'NO URL ON CHAIN! owner: {}'.format(producer['owner'])

    report['url'] = url
    try:
        bp_json = await get_bp_json(url, chain_id)
        logging.info('got bp json for {}'.format(url))
    except Exception as e:
        report['bp_json'] = 'Failed to fetch BP JSON: {}'.format(str(e))
        logging.error('Error fetching BP JSON for {}: {}'.format(url, e))
        return report

    try:
        validate_bp_json(bp_json)
    except MalformedJSONError as e:
        report['bp_json'] = 'Malformed BP JSON: {}'.format(str(e))
        return report

    report['bp_json'] = 'ok'
    logging.info('bp json for {} is valid'.format(url))

    # Check TLS version on each SSL endpoint
    ssl_endpoints = [node for node in bp_json['nodes'] if 'ssl_endpoint' in node and node['ssl_endpoint']]
    report['ssl_endpoints'] = []
    for node in ssl_endpoints:
        try:
            tlsv = await get_tls_version(node['ssl_endpoint'])
        except Exception as e:
            tlsv = 'TLS check failed: {}'.format(str(e))
            logging.error('TLS check failed for {}: {}'.format(node['ssl_endpoint'], e))

        report['ssl_endpoints'].append((node['node_type'], node['ssl_endpoint'], tlsv))

    logging.info('Checked SSL endpoint for {}'.format(url))

    # Check P2P node connect
    p2p_endpoints = [node for node in bp_json['nodes'] if 'p2p_endpoint' in node and node['p2p_endpoint']]
    report['p2p_endpoints'] = []
    for node in p2p_endpoints:
        try:
            domain, port = node['p2p_endpoint'].split(':')
            port = int(port)
            await check_port(domain, port)
            result = 'ok'
        except Exception as e:
            result = 'P2P connection failed: {}'.format(str(e))
            logging.error('P2P connection check failed for {}: {}'.format(node['p2p_endpoint'], e))

        report['p2p_endpoints'].append((node['node_type'], node['p2p_endpoint'], result))

    logging.info('Checked P2P endpoint for {}'.format(url))

    # Combine checks for SSL and API endpoints
    endpoints = {}
    for node in bp_json.get('nodes', []):
        if 'api_endpoint' in node and node['api_endpoint']:
            endpoints['HTTP'] = node['api_endpoint']
        if 'ssl_endpoint' in node and node['ssl_endpoint']:
            endpoints['HTTPS'] = node['ssl_endpoint']

    # Check each endpoint for history, default to error message if not available
    for protocol, endpoint in endpoints.items():
        try:
            early_block, late_block = await check_history(chain_url, endpoint)
            report['history'] = {protocol: {'early': early_block, 'late': late_block}}
            logging.info('Checked history for {} at {}.'.format(protocol, endpoint))
        except Exception as e:
            report['history'] = {protocol: 'History check failed: {}'.format(str(e))}
            logging.error('History check failed for {} at {}: {}'.format(protocol, endpoint, str(e)))

    # Default message if no endpoints were checked
    if not endpoints:
        report['history'] = {
            'HTTP': "Couldn't determine API endpoint for history.",
            'HTTPS': "Couldn't determine API endpoint for history."
        }
    logging.info('Checked history for {}'.format(url))

    report['cpu'] = await get_avg_performance_this_month(chain_url, bp_json['producer_account_name'])

    return report

import traceback
async def check_all_producers(
    chain_url: str,
    db_location: str = 'reports.db',
    concurrency: int = 10
):
    chain_id = await get_chain_id(chain_url)
    logging.info(f'{chain_url} chain id {chain_id}')

    # get top 42 producers ordered by vote
    producers = await get_all_producers(chain_url)

    limit = trio.CapacityLimiter(concurrency)
    reports = []
    async def get_report(_prod: dict):
        async with limit:
            try:
                report = await check_producer(chain_url, _prod, chain_id)

            except BaseException as e:
                e_text = traceback.format_exc()
                logging.critical(e_text)
                report = {
                    'url': _prod['url'],
                    'exception': e_text
                }

        reports.append(report)
        logging.info(f'finished report {len(reports)}/42')

    async with trio.open_nursery() as n:
        for producer in producers:
            n.start_soon(get_report, producer)

    return reports
