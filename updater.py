""" Update a godaddy DNS entry for a dynamic IP

My shared hosting service keeps migrating my account to a new IP.
This is probably necessary for them to lower their operational costs,
but it sucks for me. I do not use their DNS, so I must manually update
my DNS provider which each change.

This script removes the need for me to pay much attention. I may just
run it daily to keep up-to-date.

jesse@krets.com
"""
import logging
import json

import dns.resolver
from godaddypy import Client, Account

LOG = logging.getLogger('krets.dns')

def _config():
    with open("config.json", 'r') as fh:
        return json.load(fh)

class Resolver(dns.resolver.Resolver):
    def address(self, name):
        """ Convenience method to shorten interaction """
        return self.query(name).response.answer[0].items[0].address


def main():
    """ Find IPs from web host DNS and update godaddy DNS.
    """
    config = _config()

    resolver = Resolver()
    resolver.nameservers = config['initial_nameservers']
    LOG.debug("Resolving namdservers %s", config['nameservers'])
    nameservers = [resolver.address(_) for _ in config['nameservers']]

    resolver.nameservers = nameservers

    addresses = {}
    for domain in config['domains']:
        addresses[domain] = resolver.address(domain)
    LOG.debug("Found addresses: %s", addresses)

    account = Account(**config['credentials'])
    client = Client(account)
    domains = client.get_domains()

    for domain, address in addresses.items():
        if domain not in domains:
            raise ValueError("%s not in client list of domains" % domain)
        current = client.get_records(domain)[0]['data']
        if current != address:
            LOG.info('updating %s (%s -> %s)', domain, current, address)
            client.update_record_ip(address, domain, '@', 'A')
        else:
            LOG.info('Record up-to-date %s (%s)', domain, address)
    LOG.debug("complete")


if __name__ == '__main__':
    LOG.addHandler(logging.StreamHandler())
    LOG.handlers[0].setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    LOG.setLevel(logging.DEBUG)
    main()
