#!/usr/bin/env python

import json
import sys
import yaml

docs = yaml.load_all (sys.stdin)

for doc in docs:
	json.dump (doc, sys.stdout, indent = 3)
	print ''
