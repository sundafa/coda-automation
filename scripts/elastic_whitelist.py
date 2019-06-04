#!/usr/bin/env python3

"""
Input: current ansible inventory and adds some static whitelists ip
Output: applies aws elasticseach access policy
"""

import sys
import json
import pprint
import boto3

pp = pprint.PrettyPrinter(indent=4)
client = boto3.client('es')


# Read IP list from ansible inventory - FIXME: SourceOfTruth
def read_ansible_inventory(fname):
    iplist = []
    with open(fname) as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("ec2"):
                data = line.split()
                iplist.append(data[5])
    return(iplist)


if __name__ == "__main__":
    # Read currently used IPs from ansible
    proposed_ips = read_ansible_inventory("../ansible/inventory")

    # Load sensitive config
    try:
        with open('elastic_whitelist_config.json') as config_file:
            config = json.load(config_file)
    except IOError as error:
        print('Error opening secrets config:', error)
        sys.exit(1)

    # Add static whitelist ips from config.json
    for ip in config['whitelist_ips']:
        proposed_ips.append(ip)

    # Load current access policy
    response = client.describe_elasticsearch_domains(
        DomainNames=[config['elastic_domain_name']])
    for domain in response['DomainStatusList']:
        ap = domain['AccessPolicies']
    ap = json.loads(ap)

    # override ips with new set (ugly)
    current_ap_ips = ap['Statement'][0]['Condition']['IpAddress']['aws:SourceIp']
    ap['Statement'][0]['Condition']['IpAddress']['aws:SourceIp'] = proposed_ips

    # Update existing access policy
    response = client.update_elasticsearch_domain_config(
        DomainName='testnet',
        AccessPolicies=json.dumps(ap),
    )
    print('ElasticSearch Domain:', config['elastic_domain_name'])
    print('New IPs:', proposed_ips)
    print('Result:', response['ResponseMetadata']['HTTPStatusCode'])