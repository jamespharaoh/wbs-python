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
	"Resource",
]

class Resource (object):

	__slots__ = [

		"_inventory",
		"_context",
		"_name",
		"_raw_data",
		"_data",

		"_class",
		"_namespace",
		"_parent_name",

		"_unresolved",
		"_not_yet_resolved",
		"_resolved",
		"_combined",

	]

	def __init__ (self, inventory, name, raw_data):

		self._inventory = inventory
		self._context = inventory.context
		self._name = name
		self._raw_data = raw_data

		if self._raw_data ["identity"] ["type"] != "resource":

			raise Exception ()

		if name != "%s/%s" % (
			self._inventory.classes [
				self._raw_data ["identity"] ["class"]
			].namespace ().name (),
			self._raw_data ["identity"] ["name"],
		):

			raise Exception (
				"Resource name %s does not match identity name %s/%s" % (
					name,
					self._inventory.classes [
						self._raw_data ["identity"] ["class"]
					].namespace ().name (),
					self._raw_data ["identity"] ["name"]))

		self._build_identity ()
		self._build_data ()
		self._build_calculated ()

	def _build_identity (self):

		self._class = (
			self._inventory.classes [
				self._raw_data ["identity"] ["class"]])

		if "parent" in self._raw_data ["identity"]:

			self._parent_name = (
				"%s/%s" % (
					self._class.parent_namespace_name (),
					self._raw_data ["identity"] ["parent"]))

		else:

			self._parent_name = None

	def _build_data (self):

		self._data = (
			wbs.deep_copy (
				self._class.data ()))

		self._data ["identity"] = (
			wbs.deep_copy (
				self._class.resource_identity ()))

		# add resource data

		for section_name, section_data \
		in self._raw_data.items ():

			if section_name != "identity" \
			and section_name not in self._data:

				raise Exception (
					"Resource %s contains invalid section %s for class %s" % (
						self._name,
						section_name,
						self._class.name ()))

			for item_name, item_data \
			in section_data.items ():

				self._data [section_name] [item_name] = (
					wbs.deep_copy (item_data))

	def _build_calculated (self):

		self._unresolved = dict ()
		self._not_yet_resolved = dict ()
		self._combined = dict ()
		self._resolved = dict ()

		for section_name, section_data \
		in self._data.items ():

			self._unresolved [section_name] = dict ()
			self._not_yet_resolved [section_name] = dict ()
			self._combined [section_name] = dict ()
			self._resolved [section_name] = dict ()

			for item_name, item_data \
			in section_data.items ():

				self._unresolved [section_name] [item_name] = (
					wbs.deep_copy (
						item_data))

				self._not_yet_resolved [section_name] [item_name] = (
					wbs.deep_copy (
						item_data))

				self._combined [section_name] [item_name] = (
					wbs.deep_copy (
						item_data))

				full_name = (
					"%s_%s" % (
						section_name,
						item_name))

				self._unresolved [full_name] = (
					wbs.deep_copy (
						item_data))

				self._combined [full_name] = (
					wbs.deep_copy (
						item_data))

	def resolve (self, name_parts, value):

		name_combined = (
			"_".join (
				name_parts))

		if name_combined in self._resolved:

			raise Exception (
				"Attempt to resolve resource '%s' value '%s' twice" % (
					self.name (),
					name_combined))

		self._resolved [name_combined] = value
		self._combined [name_combined] = value

		if name_combined in self._not_yet_resolved:

			del self._not_yet_resolved [name_combined]

		if len (name_parts) == 1:

			pass

		elif len (name_parts) == 2:

			section_name, item_name = name_parts

			if section_name not in self._resolved:

				self._resolved [section_name] = dict ()

			if section_name not in self._combined:

				self._combined [section_name] = dict ()

			self._resolved [section_name] [item_name] = value
			self._combined [section_name] [item_name] = value

			if section_name in self._not_yet_resolved \
			and item_name in self._not_yet_resolved [section_name]:

				del self._not_yet_resolved [section_name] [item_name]

				if not self._not_yet_resolved [section_name]:
					del self._not_yet_resolved [section_name]

		else:

			raise Exception ()

	def get_unresolved (self, * name_parts):

		context = self._unresolved

		for name_part in name_parts:

			if not name_part in context:

				raise Exception (
					"Can't find unresolved '%s' in '%s' for resource '%s'" % (
						name_part,
						name_pats.join ("."),
						self.name ()))

			context = context [name_part]

		return context

	def has_unresolved (self, * name_parts):

		context = self._unresolved

		for name_part in name_parts:

			if not name_part in context:
				return False

			context = context [name_part]

		return True

	def get_resolved (self, * name_parts):

		context = self._resolved

		for name_part in name_parts:

			if not name_part in context:

				raise Exception (
					"Can't find resolved '%s' in '%s' for resource '%s'" % (
						name_part,
						".".join (name_parts),
						self.name ()))

			context = context [name_part]

		return context

	def has_resolved (self, * name_parts):

		context = self._resolved

		for name_part in name_parts:

			if not name_part in context:
				return

			context = context [name_part]

		return True

	def get (self, * name_parts):

		if self.has_resolved (* name_parts):
			return self.get_resolved (* name_parts)

		elif self.has_unresolved (* name_parts):
			return self.get_unresolved (* name_parts)

		else:

			raise Exception (
				"Can't find resolved or unresolved '%s' for resource '%s'" % (
					".".join (name_parts),
					self.name ()))

	# ----- accessors

	def classx (self):

		return self._class

	def class_back_references (self):

		return self._class.back_references ()

	def class_group_templates (self):

		return self._class.groups ()

	def class_name (self):

		return self._class.name ()

	def class_references (self):

		return self._class.references ()

	def combined (self):

		return self._combined

	def name (self):

		return self._name

	def namespace (self):

		return self._class.namespace ()

	def namespace_groups (self):

		return self._class.namespace_groups ()

	def namespace_name (self):

		return self._class.namespace_name ()

	def namespace_references (self):

		return self._class.namespace_references ()

	def parent_name (self):

		return self._parent_name

	# ----- dictionary

	def has (self, * name_parts):

		context = self._resolved

		for name_part in name_parts:

			if not name_part in context:
				return

			context = context [name_part]

		return True

	def items (self):

		return self._combined.items ()

	# ----- string representation

	def __unicode__ (self):

		return "<resource name='%s'>" % (
			self._name)

# ex: noet ts=4 filetype=python
