from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import os
import yaml

from ansible import utils
from ansible.runner.return_data import ReturnData
from ansible.utils import template

class ActionModule (object):

	TRANSFERS_FILES = False

	def __init__ (self, runner):

		self.runner = runner

	def run (
		self,
		conn,
		tmp,
		module_name,
		module_args,
		inject,
		complex_args = {},
		** kwargs
	):

		options = {}

		# read in the existing file

		if not os.path.isdir ("data/runtime"):
			os.mkdir ("data/runtime")

		filename = "data/runtime/%s" % inject ["inventory_hostname"]

		if os.path.isfile (filename):

			with open (filename) as file_handle:
				runtime_data = yaml.load (file_handle)

		else:

			runtime_data = dict ()

		for key, value in complex_args.items ():

			dynamic_key = template.template (self.runner.basedir, key, inject)

			if "." in dynamic_key:

				prefix, rest = dynamic_key.split (".", 2)

				runtime_data.setdefault (prefix, {})
				runtime_data [prefix] [rest] = value
				runtime_data [prefix + "_" + rest] = value

				options [prefix] = runtime_data [prefix]
				options [prefix + "_" + rest] = value

			else:

				runtime_data [dynamic_key] = value
				options [dynamic_key] = value

		with open (filename, "w") as file_handle:

			file_handle.write ("---\n")

			yaml.safe_dump (runtime_data, file_handle,
				default_flow_style = False,
				encoding = "utf-8",
				allow_unicode = True)

		return ReturnData (
			conn = conn,
			result = dict (
				ansible_facts = options))

# ex: noet ts=4 filetype=python
