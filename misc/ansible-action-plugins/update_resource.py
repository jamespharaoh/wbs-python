from __future__ import absolute_import
from __future__ import unicode_literals

import collections
import os
import yaml

from ansible.plugins.action import ActionBase

class ActionModule (ActionBase):

	TRANSFERS_FILES = False

	def __init__ (self, * arguments, ** keyword_arguments):

		ActionBase.__init__ (
			self,
			* arguments,
			** keyword_arguments)

	def run (self, tmp = None, task_vars = dict ()):

		options = {}
		changed = False

		# read in the existing file

		if not os.path.isdir ("data/runtime"):
			os.mkdir ("data/runtime")

		filename = "data/runtime/%s" % task_vars.get ("inventory_hostname")

		if os.path.isfile (filename):

			with open (filename) as file_handle:
				runtime_data = yaml.load (file_handle)

		else:

			runtime_data = dict ()

		for key, value in self._task.args.items ():

			dynamic_key = self._templar.template (
				key)

			if "." in dynamic_key:

				prefix, rest = dynamic_key.split (".", 2)

				runtime_data.setdefault (prefix, {})

				if runtime_data [prefix].get (rest) != value \
				or runtime_data.get (prefix + "_" + rest) != value:
					changed = True

				runtime_data [prefix] [rest] = value
				runtime_data [prefix + "_" + rest] = value

				options [prefix] = runtime_data [prefix]
				options [prefix + "_" + rest] = value

			else:

				if runtime_data.get (dynamic_key) != value:
					changed = True

				runtime_data [dynamic_key] = value
				options [dynamic_key] = value

		with open (filename, "w") as file_handle:

			file_handle.write ("---\n")

			yaml.safe_dump (runtime_data, file_handle,
				default_flow_style = False,
				encoding = "utf-8",
				allow_unicode = True)

		return dict (
			ansible_facts = options,
			changed = changed)

# ex: noet ts=4 filetype=python
