from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

#import collections
#import itertools
#import re
#import wbs

#from wbs import ReportableError
#from wbs import uprint

#from gridlinker.ansible.misc import *;

__all__ = [
	"ResourceNamespace",
]

class ResourceNamespace (object):

	__slots__ = [

		"_inventory",
		"_context",
		"_name",
		"_raw_data",
		"_data",

		"_groups",
		"_resources",

		"_references",
		"_back_references",

	]

	def __init__ (self, inventory, name, raw_data):

		self._inventory = inventory
		self._context = inventory.context
		self._name = name
		self._raw_data = raw_data

		if self._raw_data ["identity"] ["type"] != "namespace":

			raise Exception ()

		if self._raw_data ["identity"] ["name"] != name:

			raise Exception ()

		self._build_identity ()
		self._build_data ()

		self._groups = list ()
		self._resources = list ()

	def _build_identity (self):

		self._groups = (
			self._raw_data.get ("namespace", {}).get (
				"groups",
				list ()))

		self._references = (
			self._raw_data.get ("namespace", {}).get (
				"references",
				list ()))

		self._back_references = (
			self._raw_data.get ("namespace", {}).get (
				"back_references",
				list ()))

	def _build_data (self):

		self._data = dict ()

		for section_name, section_data \
		in self._raw_data.items ():

			if not isinstance (section_data, dict):

				raise Exception ()

			if section_name in [ "identity", "namespace" ]:

				continue

			self._data [section_name] = dict ()

			for item_name, item_data \
			in section_data.items ():

				self._data [section_name] [item_name] = (
					wbs.deep_copy (item_data))

	# ----- accessors

	def data (self):

		return self._data

	def groups (self):

		return self._groups

	def name (self):

		return self._name

	def references (self):

		return self._references

	def resources (self):

		return self._resources

	# ----- update methods

	def add_resource (self, resource):

		self._resources.append (
			resource)

# ex: noet ts=4 filetype=python
