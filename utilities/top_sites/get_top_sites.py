#!/usr/bin/env python
import argparse
import requests
import re
import sys

# Original Author: David Naylor

ALEXA_GLOBAL_URL = 'http://www.alexa.com/topsites/global;%d'

def main():
    sitelist = []

    page = 0
    while len(sitelist) < args.numsites:
        r = requests.get(ALEXA_GLOBAL_URL % page)

        for match in re.finditer(r'<a href="/siteinfo/(.+)">', r.text):
            sitelist.append(match.group(1))
        page += 1

    for site in sitelist[:args.numsites]:
        print 'http://%s' % site

if __name__ == "__main__":
    # set up command line args
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                                     description='Downloads a list of top sites from Alexa.')
    parser.add_argument('-n', '--numsites', default=100, help='Number of top sites to retrieve')
    args = parser.parse_args()

    args.numsites = int(args.numsites)

    main()
