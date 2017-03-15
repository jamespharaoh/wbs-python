from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

#import collections
#import itertools
#import re
import wbs

#from wbs import ReportableError
#from wbs import uprint

#from gridlinker.ansible.misc import *;

__all__ = [
	"ResourceClass",
]

class ResourceClass (object):

	__slots__ = [

		"_inventory",
		"_context",
		"_name",
		"_raw_data",
		"_data",

		"_groups",
		"_resources",
		"_namespace",
		"_parent_namespace",
		"_resource_identity",

		"_references",
		"_back_references",

	]

	def __init__ (self, inventory, name, raw_data):

		self._inventory = inventory
		self._context = inventory.context
		self._name = name
		self._raw_data = raw_data

		if self._raw_data ["identity"] ["type"] != "class":

			raise Exception ()

		if self._raw_data ["identity"] ["name"] != name:

			raise Exception ()

		self._build_identity ()
		self._build_data ()

		self._resources = list ()

	def _build_identity (self):

		self._namespace = (
			self._inventory.namespaces [
				self._raw_data ["class"] ["namespace"]])

		self._groups = (
			self._raw_data ["class"].get (
				"groups",
				list ()))

		if "parent_namespace" in self._raw_data ["class"]:

			self._parent_namespace = (
				self._inventory.namespaces [
					self._raw_data ["class"] ["parent_namespace"]])

		else:

			self._parent_namespace = None

		self._resource_identity = (
			self._raw_data ["class"].get (
				"resource_identity",
				dict ()))

		self._references = (
			self._raw_data ["class"].get (
				"references",
				list ()))

		self._back_references = (
			self._raw_data ["class"].get (
				"back_references",
				list ()))

	def _build_data (self):

		self._data = (
			wbs.deep_copy (
				self._namespace.data ()))

		# add class data

		for section_name, section_data \
		in self._raw_data.items ():

			if not isinstance (section_data, dict):

				raise Exception ()

			if section_name in [ "identity", "class" ]:

				continue

			if section_name \
			not in self._context.project_metadata ["resource_section_names"]:

				raise Exception (
					"Class %s contains unrecognised section: %s" % (
						self.name,
						section_name))

			self._data.setdefault (
				section_name,
				dict ())

			for item_name, item_data \
			in section_data.items ():

				self._data [section_name] [item_name] = (
					wbs.deep_copy (
						item_data))

		# add defaults

		for section_name, section_data \
		in self._context.project_defaults.items ():

			if section_name not in self._data:

				continue

			if not isinstance (section_data, dict):

				raise Exception (
					"Defaults section is %s but should be dictionary: %s" % (
						type (section_data),
						section_name))

			for item_name, item_value \
			in section_data.items ():

				if item_name in self._data [section_name]:

					continue

				self._data [section_name] [item_name] = (
					wbs.deep_copy (
						item_data))	

	# ----- accessors

	def back_references (self):

		return self._back_references

	def data (self):

		return self._data

	def groups (self):

		return self._groups
			
	def items (self):

		return self._data.items ()

	def name (self):

		return self._name

	def namespace (self):

		return self._namespace

	def namespace_groups (self):

		return self._namespace.groups ()

	def namespace_name (self):

		return self._namespace.name ()

	def namespace_references (self):

		return self._namespace.references ()

	def parent_namespace (self):

		return self._parent_namespace

	def parent_namespace_name (self):

		return self._parent_namespace.name ()

	def references (self):

		return self._references

	def resources (self):

		return self._resources

	def add_resource (self, resource):

		self._resources.append (
			resource)

# ex: noet ts=4 filetype=python
