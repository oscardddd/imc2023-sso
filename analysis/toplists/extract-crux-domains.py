#!/usr/bin/env python3

# get just the domain + public suffix from a URL

import tldextract

with open('../data/crux/202212.csv', 'r') as f:
    # skip the first readline
    for line in f.readlines()[1:1001]:
        # line: https://czbooks.net,1000
        ext = tldextract.extract(line.split(",")[0])
        print('.'.join([ext.domain, ext.suffix]))
