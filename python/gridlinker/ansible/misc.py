from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

__ALL__ = [
	"ansible_escape",
]

def ansible_escape (value):

	if isinstance (value, dict):

		return dict ([
			(item_key, ansible_escape (item_value))
			for item_key, item_value in value.items ()
		])

	elif isinstance (value, list):

		return list ([
			ansible_escape (item)
			for item in value
		])

	else:

		return value.replace (
			"{{",
			"{{ '{{' }}")

# ex: noet ts=4 filetype=python
