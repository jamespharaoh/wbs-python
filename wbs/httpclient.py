from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib

def urlencode (data):

	if isinstance (data, str):

		return urllib.quote_plus (
			data)

	elif isinstance (data, unicode):

		return urllib.quote_plus (
			data.encode ("utf-8"))

	elif isinstance (data, dict):

		return str ("&").join ([
			str ("%s=%s") % (
				urlencode (key),
				urlencode (value),
			)
			for key, value
			in data.items ()
		])

	else:

		return "Cannot url encode %s" % type (data)

# ex: noet ts=4 filetype=python
