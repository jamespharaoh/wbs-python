from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import collections
import itertools
import re
import wbs

from wbs import ReportableError
from wbs import uprint

from gridlinker.ansible.misc import *;

__all__ = [
	"Inventory",
]

class ResourceNamespace (object):

	__slots__ = [

		"name",
		"data",

		"groups",
		"resources",

		"references",
		"back_references",

	]

	def __init__ (self, name, data):

		assert data ["identity"] ["type"] == "namespace"
		assert data ["identity"] ["name"] == name

		self.name = name
		self.data = data

		self.groups = data.get ("namespace", {}).get ("groups", [])
		self.resources = list ()

		self.references = (
			data.get ("namespace", {}).get (
				"references",
				list ()))

		self.back_references = (
			data.get ("namespace", {}).get (
				"back_references",
				list ()))

	def add_resource (self, resource):

		self.resources.append (
			resource)

class ResourceClass (object):

	__slots__ = [

		"data",

		"name",

		"groups",
		"resources",
		"namespace",
		"parent_namespace",
		"resource_identity",

		"references",
		"back_references",

	]

	def __init__ (self, inventory, data):

		context = inventory.context
		project_metadata = context.project_metadata

		self.data = data

		self.name = data ["identity"] ["name"]

		self.namespace = data ["class"] ["namespace"]
		self.groups = data ["class"].get ("groups", [])
		self.resources = list ()

		self.parent_namespace = (
			data ["class"].get (
				"parent_namespace",
				None))

		self.resource_identity = (
			data ["class"].get (
				"resource_identity",
				dict ()))

		self.references = (
			data ["class"].get (
				"references",
				list ()))

		self.back_references = (
			data ["class"].get (
				"back_references",
				list ()))

		for section_name, section_data in self.data.items ():

			if section_name in [ "identity", "class" ]:

				continue

			if section_name \
			not in project_metadata ["resource_section_names"]:

				raise Exception (
					"Class %s contains unrecognised section: %s" % (
						self.name,
						section_name))

	def items (self):

		return self.data.items ()

	def add_resource (self, resource):

		self.resources.append (
			resource)

class Resource (object):

	__slots__ = [

		"data",

		"unique_name",
		"identity_class",
		"identity_name",
		"identity_namespace",
		"identity_parent",

		"resource_class",
		"resource_namespace",

		"unresolved",
		"not_yet_resolved",
		"resolved",
		"combined",

	]

	def __init__ (self, inventory, data):

		context = inventory.context

		self.data = data

		self.identity_class = data ["identity"] ["class"]
		self.identity_name = data ["identity"] ["name"]
		self.identity_parent = data ["identity"].get ("parent")

		self.resource_class = (
			inventory.classes [self.identity_class])

		self.identity_namespace = (
			self.resource_class.namespace)

		self.resource_namespace = (
			inventory.namespaces [self.identity_namespace])

		data ["identity"] ["namespace"] = (
			self.resource_namespace.name)

		data ["identity_namespace"] = (
			self.resource_namespace.name)

		self.unique_name = "/".join ([
			self.identity_namespace,
			self.identity_name,
		])

		data ["unique_name"] = self.unique_name

		# add resource data

		self.unresolved = wbs.deep_copy (data)
		self.not_yet_resolved = wbs.deep_copy (data)
		self.combined = wbs.deep_copy (data)
		self.resolved = dict ()

		for section_name, section_data in data.items ():

			if not isinstance (section_data, dict):
				continue

			for item_name, item_value \
			in section_data.items ():

				self.unresolved [section_name + "_" + item_name] = (
					item_value)

				self.combined [section_name + "_" + item_name] = (
					item_value)

		# add class data

		for section_name, section_data \
		in self.resource_class.items ():

			if section_name in [ "identity", "class" ]:
				continue

			if not section_name in self.unresolved:

				self.unresolved [section_name] = (
					collections.OrderedDict ())

			if not isinstance (
				self.unresolved [section_name],
				dict):

				raise Exception (
					"Not a dictionary: %s.%s" % (
						self.unique_name,
						section_name))

			if not section_name in self.not_yet_resolved:

				self.not_yet_resolved [section_name] = (
					collections.OrderedDict ())

			if not section_name in self.combined:

				self.combined [section_name] = (
					collections.OrderedDict ())

			for item_name, item_value \
			in section_data.items ():

				if item_name in self.unresolved [section_name]:
					continue

				self.unresolved [section_name] [item_name] = (
					item_value)

				self.not_yet_resolved [section_name] [item_name] = (
					item_value)

				self.combined [section_name] [item_name] = (
					item_value)

				full_name = (
					"%s_%s" % (
						section_name,
						item_name))

				self.unresolved [full_name] = (
					item_value)

				self.combined [full_name] = (
					item_value)

		# add namespace data

		for namespace_prefix, namespace_data \
		in self.resource_namespace.data.items ():

			if namespace_prefix in [ "identity", "namespace" ]:
				continue

			if not namespace_prefix in self.unresolved:

				self.unresolved [namespace_prefix] = (
					collections.OrderedDict ())

			if not namespace_prefix in self.not_yet_resolved:

				self.not_yet_resolved [namespace_prefix] = (
					collections.OrderedDict ())

			if not namespace_prefix in self.combined:

				self.combined [namespace_prefix] = (
					collections.OrderedDict ())

			if not isinstance (
				self.unresolved [namespace_prefix],
				dict):

				raise Exception (
					"Not a dictionary: %s.%s" % (
						self.unique_name,
						namespace_prefix))

			for section_name, section_value \
			in namespace_data.items ():

				if section_name in self.unresolved [namespace_prefix]:
					continue

				self.unresolved [namespace_prefix] [section_name] = (
					section_value)

				self.not_yet_resolved [namespace_prefix] [section_name] = (
					section_value)

				self.combined [namespace_prefix] [section_name] = (
					section_value)

				full_name = (
					"%s_%s" % (
						namespace_prefix,
						section_name))

				self.unresolved [full_name] = (
					section_value)

				self.combined [full_name] = (
					section_value)

		# add defaults

		for section_name, section_data \
		in self.combined.items ():

			if not isinstance (section_data, dict):
				continue

			for item_name, item_value \
			in context.project_defaults.get (section_name, {}).items ():

				if section_name + "_" + item_name not in self.unresolved:

					self.unresolved [section_name + "_" + item_name] = (
						wbs.deep_copy (item_value))

				if section_name + "_" + item_name not in self.not_yet_resolved:

					self.not_yet_resolved [section_name + "_" + item_name] = (
						wbs.deep_copy (item_value))

				if section_name + "_" + item_name not in self.combined:

					self.combined [section_name + "_" + item_name] = (
						wbs.deep_copy (item_value))

				if item_name not in self.unresolved [section_name]:

					self.unresolved [section_name] [item_name] = (
						wbs.deep_copy (item_value))

				if item_name not in self.not_yet_resolved [section_name]:

					self.not_yet_resolved [section_name] [item_name] = (
						wbs.deep_copy (item_value))

				if item_name not in self.combined [section_name]:

					self.combined [section_name] [item_name] = (
						wbs.deep_copy (item_value))

		for identity_name, identity_value \
		in self.resource_class.resource_identity.items ():

			if identity_name \
			not in self.unresolved ["identity"]:

				if identity_name in self.unresolved ["identity"]:
					continue

				identity_full_name = (
					"identity_%s" % (
						identity_name))

				self.unresolved ["identity"] [identity_name] = (
					identity_value)

				self.not_yet_resolved ["identity"] [identity_name] = (
					identity_value)

				self.combined ["identity"] [identity_name] = (
					identity_value)

				self.unresolved [identity_full_name] = (
					identity_value)

				self.combined [identity_full_name] = (
					identity_value)

	def resolve (self, name_parts, value):

		name_combined = (
			"_".join (
				name_parts))

		if name_combined in self.resolved:

			raise Exception (
				"Attempt to resolve resource '%s' value '%s' twice" % (
					self.unique_name,
					name_combined))

		self.resolved [name_combined] = value
		self.combined [name_combined] = value

		if name_combined in self.not_yet_resolved:

			del self.not_yet_resolved [name_combined]

		if len (name_parts) == 1:

			pass

		elif len (name_parts) == 2:

			section_name, item_name = name_parts

			if section_name not in self.resolved:
				self.resolved [section_name] = dict ()

			if section_name not in self.combined:
				self.combined [section_name] = dict ()

			self.resolved [section_name] [item_name] = value
			self.combined [section_name] [item_name] = value

			if section_name in self.not_yet_resolved \
			and item_name in self.not_yet_resolved [section_name]:

				del self.not_yet_resolved [section_name] [item_name]

				if not self.not_yet_resolved [section_name]:
					del self.not_yet_resolved [section_name]

		else:

			raise Exception ()

	def get_unresolved (self, * name_parts):

		context = self.unresolved

		for name_part in name_parts:

			if not name_part in context:

				raise Exception (
					"Can't find unresolved '%s' in '%s' for resource '%s'" % (
						name_part,
						name_pats.join ("."),
						self.unique_name))

			context = context [name_part]

		return context

	def has_unresolved (self, * name_parts):

		context = self.unresolved

		for name_part in name_parts:

			if not name_part in context:
				return False

			context = context [name_part]

		return True

	def get_resolved (self, * name_parts):

		context = self.resolved

		for name_part in name_parts:

			if not name_part in context:

				raise Exception (
					"Can't find resolved '%s' in '%s' for resource '%s'" % (
						name_part,
						".".join (name_parts),
						self.unique_name))

			context = context [name_part]

		return context

	def has_resolved (self, * name_parts):

		context = self.resolved

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
					self.unique_name))

	def has (self, * name_parts):

		context = self.resolved

		for name_part in name_parts:

			if not name_part in context:
				return

			context = context [name_part]

		return True

	def items (self):

		return self.combined.items ()

	def __unicode__ (self):

		return self.unique_name

class Inventory (object):

	___slots__ = [

		"context",
		"trace",

		"world",
		"classes",
		"groups",
		"resources",
		"namespaces",

		"group_children",
		"group_members",
		"resource_children",
		"class_groups",

	]

	def __init__ (self, context):

		self.context = context
		self.trace = context.trace

		self.world = {}

		self.classes = {}
		self.groups = {}
		self.resources = {}
		self.namespaces = {}

		self.group_children = collections.defaultdict (list)
		self.group_members = collections.defaultdict (list)

		self.resource_children = collections.defaultdict (list)

		self.class_groups = set ()

		self.load_world ()

	def load_world (self):

		self.all = {

			"NAME": self.context.project_metadata ["project"] ["name"],
			"SHORT_NAME": self.context.project_metadata ["project"] ["short_name"],
			"SHORT_TITLE": self.context.project_metadata ["project"] ["short_title"],

			"HOME": self.context.home,
			"WORK": "%s/work" % self.context.home,
			"GRIDLINKER_HOME": self.context.gridlinker_home,

			"CONNECTION": self.context.connection_name,

			"CLASSES": ansible_escape (dict ([
				(class_name, class_data)
				for class_directory_name, class_directory
				in self.context.local_data ["classes"].items ()
				for class_name, class_data
				in class_directory.items ()
			])),

			"DEFAULTS": ansible_escape (
				self.context.local_data ["defaults"]),

			"GLOBALS": ansible_escape (
				self.context.local_data ["globals"]),

			"METADATA": ansible_escape (
				self.context.project_metadata_stripped),

			"NAMESPACES": ansible_escape (
				self.context.local_data ["namespaces"]),

			"PROJECT": ansible_escape (
				self.context.project_metadata ["project"]),

			"PROJECT_DATA": ansible_escape (
				self.context.project_metadata ["project_data"]),

			"RESOURCE_DATA": ansible_escape (
				self.context.project_metadata ["resource_data"]),

		}

		if "globals" in self.context.local_data:

			for prefix, data in self.context.local_data ["globals"].items ():

				self.all [prefix] = data

				if isinstance (data, dict):

					for name, value in data.items ():
						self.all [prefix + "_" + name] = value

		self.load_namespaces ()
		self.load_classes ()
		self.load_resources_1 ()
		self.load_resources_2 ()
		self.resolve_resource_values ()
		self.resolve_parents ()
		self.resolve_references ()
		self.resolve_back_references ()
		self.resolve_resource_values ()
		self.load_resources_5 ()

		self.all ["GROUPS"] = dict ([
			(group_name, {
				"type": "group",
				"name": group_name,
				"members": group_member_names,
			})
			for group_name, group_member_names
			in self.group_members.items ()
		])

	def load_namespaces (self):

		for namespace_name, namespace_data \
		in self.context.namespaces.items ():

			self.namespaces [namespace_name] = (
				ResourceNamespace (
					namespace_name,
					namespace_data))

	def load_classes (self):

		for class_name, class_data \
		in self.context.classes.items ():

			self.add_class (
				class_name,
				class_data)

	def add_class (self, class_name, class_data):

		# check basics

		if not "identity" in class_data:

			raise Exception (
				"Invalid class definition: %s" % class_name)

		if class_data ["identity"] ["type"] != "class":

			raise Exception (
				"Class does not contain correct type: %s" % class_name)

		if class_name != class_data ["identity"] ["name"]:

			raise Exception (
				"Class does not contain correct name: %s" % class_name)

		# check for duplicates

		if class_name in self.world:

			raise Exception (
				"Class is duplicated: %s" % class_name)

		# create class

		resource_class = (
			ResourceClass (
				self,
				class_data))

		# store class

		self.world [class_name] = resource_class
		self.classes [class_name] = resource_class

	def load_resources_1 (self):

		for resource_name, resource_data \
		in self.context.resources.get_all_list_quick ():

			resource_data = (
				wbs.deep_copy (
					resource_data))

			# check basics

			if not "identity" in resource_data:
				raise Exception ()

			if resource_data ["identity"] ["type"] != "resource":

				raise Exception (
					"Invalid type '%s' for resource '%s'" % (
						resource_data ["identity"] ["type"],
						resource_name))

			# create resource

			self.add_resource (
				resource_data)

	def add_resource (
			self,
			resource_data):

		resource = (
			Resource (
				self,
				resource_data))

		if resource.unique_name in self.world:
			raise Exception ()

		self.world [resource.unique_name] = resource
		self.resources [resource.unique_name] = resource

		self.group_members [resource.identity_class].append (
			resource.unique_name)

		if not resource.identity_namespace in self.namespaces:

			raise Exception (
				"Resource '%s' has invalid namespace '%s'" % (
					resource.unique_name,
					resource.identity_namespace))

		self.classes [resource.identity_class].add_resource (
			resource)

		self.namespaces [resource.identity_namespace].add_resource (
			resource)

	def load_resources_2 (self):

		for resource_name, resource \
		in self.resources.items ():

			# set identity parent and grandparent

			if resource.has_unresolved ("identity", "parent"):

				parent_name = (
					"%s/%s" % (
						resource.resource_class.parent_namespace,
						resource.identity_parent))

				if not parent_name in self.resources:

					raise Exception (
						"Can't find parent of %s: %s" % (
							resource_name,
							parent_name))

				parent_resource = (
					self.resources [
						parent_name])

				self.resource_children [parent_name].append (resource_name)

				if parent_resource.has_unresolved ("identity", "parent"):

					resource.resolve (
						[ "identity", "grandparent" ],
						parent_resource.get_unresolved ("identity", "parent"))

		# set children

		for resource_name, resource \
		in self.resources.items ():

			resource.resolve (
				[ "identity", "children" ],
				self.resource_children [resource_name])

	def resolve_resource_values (self):

		num_resolved = None
		pass_count = 0

		while num_resolved is None or num_resolved > 0:

			if self.trace:

				uprint (
					"resolve_resource_values () pass %s" % (
						pass_count + 1))

			num_resolved = 0

			for resource \
			in self.resources.values ():

				num_resolved += (
					self.resolve_resource_values_one (
						resource))

			pass_count += 1

	def resolve_resource_values_one (self, resource):

		num_resolved = 0

		for prefix, data \
		in resource.not_yet_resolved.items ():

			if isinstance (data, dict):

				for name, value in data.items ():

					if self.trace:

						uprint (
							"  resolve %s.%s.%s" % (
								resource.unique_name,
								prefix,
								name))

					full_name = "_".join ([
						prefix,
						name,
					])

					if full_name in resource.resolved:
						continue

					success, resolved = (
						self.resolve_value_real (
							resource,
							value,
							"    "))

					if not success:

						if self.trace:

							uprint (
								"    failed to resolve")

						continue

					resource.resolve (
						[ prefix, name ],
						resolved)

					if self.trace:

						uprint (
							"    resolved successfully")

					num_resolved += 1

			elif prefix not in resource.resolved:

				if self.trace:

					uprint (
						"  resolve %s.%s" % (
							resource.unique_name,
							prefix))

				success, resolved = (
					self.resolve_value_real (
						resource,
						data,
						"  "))

				if not success:
					continue

				resource.resolve (
					[ prefix ],
					resolved)

				if self.trace:

					uprint (
						"    resolved successfully")

				num_resolved += 1

		return num_resolved

	def resolve_parents (self):

		for resource_name, resource \
		in self.resources.items ():

			if "parent" in resource.data ["identity"]:

				parent_name = (
					"%s/%s" % (
						resource.resource_class.parent_namespace,
						resource.identity_parent))

				resource.resolve (
					[ "parent" ],
					"{{ hostvars ['%s'] }}" % (
						parent_name))

				if resource.has ("identity", "grandparent"):

					parent = self.resources [parent_name]

					grandparent_name = (
						"%s/%s" % (
							parent.resource_class.parent_namespace,
							parent.identity_parent))

					resource.resolve (
						[ "grandparent" ],
						"{{ hostvars ['%s'] }}" % (
							grandparent_name))

	def resolve_references (self):

		for resource_name, resource \
		in self.resources.items ():

			reference_names = set ()

			for reference \
			in itertools.chain (
				resource.resource_class.references,
				resource.resource_namespace.references,
			):

				if reference ["name"] in reference_names:
					continue

				reference_names.add (
					reference ["name"])

				if reference ["type"] == "resource":

					target_name = (
						self.resolve_value_or_fail (
							resource_name,
							reference ["value"],
							""))

					if not target_name in self.resources:

						raise ReportableError (
							"inventory_referenced_resource_does_not_exist",
							resource_name = resource_name,
							referenced_resource_name = target_name,
							reference_name = reference ["name"])

					if "section" in reference:

						resource.resolve (
							[ reference ["name"] ],
							"{{ hostvars ['%s'] }}.%s" % (
								target_name,
								reference ["section"]))

					else:

						resource.resolve (
							[ reference ["name"] ],
							"{{ hostvars ['%s'] }}" % (
								target_name))

				elif reference ["type"] == "simple":

					resource.resolve (
						[ reference ["name"] ],
						reference ["value"])

				else:

					raise Exception ()

	def resolve_back_references (self):

		for resource_name, resource \
		in self.resources.items ():

			for back_reference \
			in resource.resource_class.back_references:

				if back_reference ["type"] == "resource":

					namespace = back_reference ["namespace"]
					field = back_reference ["field"]

					section = back_reference ["section"]
					name = back_reference ["name"]

					values = []

					for other_resource \
					in self.namespaces [namespace].resources:

						if not other_resource.has (field):
							continue

						other_values = (
							other_resource.get (
								field))

						if not isinstance (other_values, list):
							other_values = [ other_values ]

						if not resource.identity_name in other_values:
							continue

						values.append (
							other_resource.identity_name)

					resource.resolve (
						[ section, name ],
						values)

				else:

					raise Exception ()

	def load_resources_5 (self):

		for resource_name, resource \
		in self.resources.items ():

			# namespace groups

			for group_template \
			in resource.resource_namespace.groups:

				group_name = (
					self.resolve_value_or_none (
						resource_name,
						group_template,
						""))

				if not group_name:
					continue

				if not group_name in self.class_groups:

					if group_name in self.world:
						raise Exception ()

					self.class_groups.add (
						group_name)

				self.group_members [group_name].append (
					resource_name)

			# class groups

			for group_template \
			in resource.resource_class.groups:

				group_name = (
					self.resolve_value_or_none (
						resource_name,
						group_template,
						""))

				if not group_name:
					continue

				if not group_name in self.class_groups:

					if group_name in self.world:
						raise Exception ()

					self.class_groups.add (
						group_name)

				self.group_members [group_name].append (
					resource_name)

	def add_group_class_type (self,
			item_friendly_name,
			item_short_name,
			item_data):

		item_name = item_data [item_short_name + "_name"]

		if item_short_name + "_group" in item_data:

			# add to group

			item_group = item_data [item_short_name + "_group"]

			if not item_group in all_groups:

				raise Exception (
					"%s %s has invalid group: %s" % (
						item_friendly_name,
						item_name,
						item_group))

			group_data = all_groups [item_group]

			all_groups [item_group] ["hosts"].append (item_name)

			# add to class

			group_class = group_data ["vars"] ["group_class"]

			if not group_class in all_groups:

				raise Exception ()

			class_data = all_groups [group_class]

			all_groups [group_class] ["hosts"].append (item_name)

			# add to type

			group_type = class_data ["vars"] ["class_type"]

			if not group_type in all_groups:

				raise Exception ()

			type_data = all_groups [group_type]

			all_groups [group_type] ["hosts"].append (item_name)

		elif item_short_name + "_class" in item_data:

			item_class = item_data [item_short_name + "_class"]
			class_data = all_groups [item_class]
			all_groups [item_class] ["hosts"].append (item_name)

			group_type = class_data ["vars"] ["class_type"]
			type_data = all_groups [group_type]
			all_groups [group_type] ["hosts"].append (item_name)

	def resolve_group (self, group_name, group_data):

		group_vars = group_data.get ("global", {})

		for prefix, data in group_data.items ():

			if prefix == "identity":
				continue

			group_vars [prefix] = data

		return group_vars

	def resolve_class (self, class_name, class_data):

		class_vars = class_data.get ("global", {})

		for prefix, data in class_data.items ():

			if prefix == "identity":
				continue

			class_vars [prefix] = data

		return class_vars

	def find_resource (
			self,
			source):

		if isinstance (source, Resource):
			return source

		elif isinstance (source, str) \
		or isinstance (source, unicode):

			if not source in self.resources:

				raise Exception (
					"No such resource: %s",
					source)

			return self.resources [source]

		else:

			raise Exception ()

	def resolve_value_or_fail (
			self,
			resource_source,
			value,
			indent = ""):

		resource = (
			self.find_resource (
				resource_source))

		success, resolved = (
			self.resolve_value_real (
				resource_source = resource,
				value = value,
				indent = indent))

		if not success:

			raise Exception (
				"Unable to resolve '%s' for resource '%s'" % (
					value,
					resource.unique_name))

		return resolved

	def resolve_value_or_same (
			self,
			resource_source,
			value,
			indent):

		resource = (
			self.find_resource (
				resource_source))

		success, resolved = (
			self.resolve_value_real (
				resource_source = resource,
				value = value,
				indent = indent))

		if not success:
			return value

		return resolved

	def resolve_value_or_none (
			self,
			resource_source,
			value,
			indent):

		resource = (
			self.find_resource (
				resource_source))

		success, resolved = (
			self.resolve_value_real (
				resource_source = resource,
				value = value,
				indent = indent))

		if not success:
			return None

		return resolved

	def resolve_value_real (
			self,
			resource_source,
			value,
			indent):

		resource = (
			self.find_resource (
				resource_source))

		if self.trace:

			uprint (
				"%sresolve_value (%s, %s)" % (
					indent,
					resource.unique_name,
					value))

			indent = indent + "  "

		if isinstance (value, list):

			ret = []

			for item in value:

				success, resolved = (
					self.resolve_value_real (
						resource,
						item,
						indent + "  "))

				if not success:
					return False, None

				ret.append (resolved)

			return True, ret

		elif isinstance (value, dict):

			ret = collections.OrderedDict ()

			for key, item in value.items ():

				success, resolved = (
					self.resolve_value_real (
						resource,
						item,
						indent + "  "))

				if not success:
					return False, None

				ret [key] = resolved

			return True, ret

		elif isinstance (value, str) \
		or isinstance (value, unicode):

			match = (
				re.search (
					r"^\{\{\s*([^{}]*\S)\s*\}\}$",
					value))

			if match:

				return self.resolve_expression (
					resource,
					match.group (1),
					indent + "  ")

			else:

				ret = ""
				last_pos = 0

				for match in re.finditer (r"\{\{\s*(.*?)\s*\}\}", value):

					ret += value [last_pos : match.start ()]

					success, resolved = (
						self.resolve_expression (
							resource,
							match.group (1),
							indent + "  "))

					if not success:
						return False, None

					ret += unicode (resolved)

					last_pos = match.end ()

				ret += value [last_pos :]

				return True, ret

		else:

			return False, None

	def resolve_expression (
			self,
			resource_source,
			name,
			indent):

		resource = (
			self.find_resource (
				resource_source))

		if self.trace:

			uprint (
				"%sresolve_expression (%s, %s)" % (
					indent,
					resource.unique_name,
					name))

			indent = indent + "  "

		success, tokens = (
			self.tokenize (name))

		if not success:

			if self.trace:

				uprint (
					"%stokenize failed" % (
						indent))

			return False, None

		if self.trace:

			uprint (
				"%stokens: '%s'" % (
					indent,
					"', '".join (tokens)))

		token_index = 0

		success, token_index, value = (
			self.parse_expression (
				tokens,
				token_index,
				resource,
				indent + "  "))

		if not success:

			if self.trace:

				uprint (
					"%sparse failed" % (
						indent))

			return False, None

		if token_index < len (tokens):

			if self.trace:

				uprint (
					"%sonly used %s/%s tokens" % (
						indent,
						token_index,
						len (tokens)))

			return False, None

		if self.trace:

			uprint (
				"%ssuccess: %s" % (
					indent,
					value))

		return True, value

	def parse_expression (
			self,
			tokens,
			token_index,
			resource_source,
			indent):

		resource = (
			self.find_resource (
				resource_source))

		if self.trace:

			uprint (
				"%sparse_expression ([ '%s' ], %s, %s)" % (
					indent,
					"', '".join (tokens),
					token_index,
					resource.unique_name))

			indent = indent + "  "

		success, token_index, value_type, value = (
			self.parse_simple (
				tokens,
				token_index,
				resource,
				indent + "  "))

		if not success:

			return False, None, None

		while token_index < len (tokens):

			if tokens [token_index] == ".":

				if self.trace:

					uprint (
						"%sparse simple attribute - x.y" % (
							indent))

				token_index += 1
				token = tokens [token_index]
				token_index += 1

				success, value_type, value = (
					self.dereference (
						value_type,
						value,
						token,
						indent + "  "))

				if success:

					if self.trace:

						uprint (
							"%sresult - .%s = %s: %s" % (
								indent,
								token,
								value_type,
								value))

					continue

				else:

					if self.trace:

						uprint (
							"%svalue not present: %s" % (
								indent,
								token))

					return False, None, None

			elif tokens [token_index] == "|":

				token_index += 1

				if tokens [token_index] == "keys" \
				and value_type == "value":

					token_index += 1

					value = value.keys ()

					continue

				if tokens [token_index] == "values" \
				and value_type == "value":

					token_index += 1

					value = value.values ()

					continue

				if tokens [token_index] == "join" \
				and value_type == "value" \
				and isinstance (value, list):

					token_index += 1

					value = "".join (value)

					continue

				if tokens [token_index + 0] == "union" \
				and tokens [token_index + 1] == "(" \
				and value_type == "value" \
				and isinstance (value, list):

					token_index += 2

					success, token_index, union_value = (
						self.parse_expression (
							tokens,
							token_index,
							resource,
							indent + "  "))

					if not success:

						return False, None, None

					if not isinstance (union_value, list):

						return False, None, None

					if tokens [token_index] != ")":

						return False, None, None

					token_index += 1

					item_set = set ()

					new_value = list ()

					for item in value + union_value:

						if isinstance (item, dict):

							new_value.append (
								item)

						elif item not in item_set:

							new_value.append (
								item)

							item_set.add (
								item)

					value = new_value

					continue

				if tokens [token_index + 0] == "substring_before" \
				and tokens [token_index + 1] == "(" \
				and tokens [token_index + 2] [0] == "'" \
				and tokens [token_index + 3] == ")":

					separator = (
						re.sub (
							r"\\(.)",
							lambda match: match.group (1),
							tokens [token_index + 2] [1 : -1]))

					token_index += 4

					if value_type == "value":

						value = (
							value.partition (separator) [0])

						continue

					raise Exception ()

				if tokens [token_index + 0] == "not_empty_string" \
				and value_type == "value":

					token_index += 1

					string_value = (
						unicode (
							value))

					if string_value != "":

						value = string_value

					else:

						return False, None, None

					continue

				if tokens [token_index + 0] == "default" \
				and tokens [token_index + 1] == "(" \
				and value_type == "value":

					token_index += 2

					success, token_index, default_value = (
						self.parse_expression (
							tokens,
							token_index,
							resource,
							indent + "  "))

					if not success:

						return False, None, None

					if tokens [token_index] != ")":

						return False, None, None

					token_index += 1

					if value is None:

						value = default_value

					continue

				return False, None, None

			elif tokens [token_index + 0] == "if" \
			and value_type == "value":

				token_index += 1

				success, token_index, test_value = (	
					self.parse_expression (
						tokens,
						token_index,
						resource,
						indent + "  "))

				if not success:

					return False, None, None

				if tokens [token_index] != "else":

					return False, None, None

				token_index += 1

				success, token_index, false_value = (
					self.parse_expression (
						tokens,
						token_index,
						resource,
						indent + "  "))

				if not success:

					return False, None, None

				if not test_value:

					value = false_value

				continue

			elif tokens [token_index + 0] == "==" \
			and value_type == "value":

				token_index += 1

				success, token_index, right_value = (
					self.parse_expression (
						tokens,
						token_index,
						resource,
						indent + "  "))

				if not success:

					return False, None, None

				value = (value == right_value)

				continue

			elif tokens [token_index + 0] == "!=" \
			and value_type == "value":

				token_index += 1

				success, token_index, right_value = (
					self.parse_expression (
						tokens,
						token_index,
						resource,
						indent + "  "))

				if not success:

					return False, None, None

				value = (value != right_value)

				continue

			elif tokens [token_index + 0] == "+" \
			and value_type == "value":

				if self.trace:

					uprint (
						"%sparse addition - %s + ?" % (
							indent,
							value))

				token_index += 1

				success, token_index, right_value = (
					self.parse_expression (
						tokens,
						token_index,
						resource,
						indent + "  "))

				if not success:

					return False, None, None

				value = (value + right_value)

				if self.trace:

					uprint (
						"%sresult: + %s = %s" % (
							indent,
							right_value,
							value))

				continue

			elif tokens [token_index] == "[":

				if self.trace:

					uprint (
						"%sparse dynamic attribute - x [y]" % (
							indent))

				token_index += 1

				success, token_index, resolved_value = (
					self.parse_expression (
						tokens,
						token_index,
						resource,
						indent + "  "))

				if not success:

					return False, None, None

				if tokens [token_index] != "]":

					return False, None, None

				token_index += 1

				if self.trace:

					uprint (
						"%sresolved index: %s" % (
							indent,
							resolved_value))

				if value_type == "resource":

					success, value_type, value = (
						self.dereference_resource (
						value,
						resolved_value,
						indent + "  "))

					if success:

						if self.trace:

							uprint (
								"%sresult: [%s] = %s" % (
									indent,
									resolved_value,
									value))

						continue

				elif value_type == "value":

					if resolved_value in value:

						value = value [resolved_value]

						if self.trace:

							uprint (
								"%sresult: [%s] = %s" % (
									indent,
									resolved_value,
									value))

						continue

					elif str (resolved_value) in value:

						value = value [str (resolved_value)]

						if self.trace:

							uprint (
								"%sresult: [%s] = %s" % (
									indent,
									resolved_value,
									value))

						continue

				elif value_type == "hostvars":

					if resolved_value in self.resources:

						value_type = "resource"
						value = resolved_value

						if self.trace:

							uprint (
								"%sresult: [%s] = resource: %s" % (
									indent,
									resolved_value,
									value))

						continue

				if self.trace:

					uprint (
						"%svalue not present: %s" % (
							indent,
							resolved_value))

				return False, None, None

			else:

				break

		return True, token_index, value

	def parse_simple (
			self,
			tokens,
			token_index,
			resource_source,
			indent):

		if self.trace:

			uprint (
				"%sparse_simple ([ '%s' ], %s, %s)" % (
					indent,
					"', '".join (tokens),
					token_index,
					resource_source))

			indent = indent + "  "

		token = (
			tokens [token_index])

		resource = (
			self.find_resource (
				resource_source))

		if token [0] == "'":

			string_value = (
				re.sub (
					r"\\(.)",
					lambda match: match.group (1),
					token [1 : -1]))

			return True, token_index + 1, "value", string_value

		if token == "(":

			new_token_index = (
				token_index + 1)

			success, new_token_index, value = (
				self.parse_expression (
					tokens,
					new_token_index,
					resource,
					indent + "  "))

			if not success:

				return False, token_index, None, None

			if tokens [new_token_index] != ")":

				return False, token_index, None, None

			return True, new_token_index + 1, "value", value

		if token == "[":

			if self.trace:

				uprint (
					"%sparse dynamic lookup - x [y]" % (
						indent))

			new_token_index = (
				token_index + 1)

			items = []

			while tokens [new_token_index] != "]":

				success, new_token_index, item = (
					self.parse_expression (
						tokens,
						new_token_index,
						resource,
						indent + "  "))

				if not success:

					return False, token_index, None, None

				items.append (
					item)

				if tokens [new_token_index] == ",":

					new_token_index += 1

				elif tokens [new_token_index] != "]":

					return False, token_index, None, None

			return True, new_token_index + 1, "value", items

		if token == "hostvars":

			if self.trace:

				uprint (
					"%srecurse hostvars" % (
						indent))

			return True, token_index + 1, "hostvars", None

		if token in self.context.project_metadata ["project_data"]:

			if self.trace:

				uprint (
					"%sfound in project data: %s" % (
						indent,
						token))

			unresolved_value = (
				self.context.local_data [
					self.context.project_metadata ["project_data"] [token]])

			success, resolved_value = (
				self.resolve_value_real (
					resource,
					unresolved_value,
					indent + "  "))

			if not success:

				return False, None, None, None

			else:

				return True, token_index + 1, "value", resolved_value

		success, value_type, value = (
			self.dereference_resource (
				resource,
				token,
				indent))

		if success:

			return True, token_index + 1, value_type, value

		if self.trace:

			uprint (
				"%sunable to resolve: %s" % (
					indent,
					token))

		return False, token_index, None, None

	def dereference (
			self,
			reference_type,
			reference_value,
			token,
			indent):

		if self.trace:

			uprint (
				"%sdereference (%s, %s, %s)" % (
					indent,
					reference_type,
					reference_value,
					token))

			indent += "  "

		if reference_type == "resource":

			return self.dereference_resource (
				reference_value,
				token,
				indent + "  ")

		elif reference_type == "resource-section":

			value_resource_name, value_section_name = (
				reference_value.split ("."))

			return self.dereference_resource (
				value_resource_name,
				value_section_name + "_" + token,
				indent + "  ")

		elif reference_type == "value":

			if not isinstance (reference_value, dict):

				if self.trace:

					uprint (
						"%sCan't dereference '%s' from a %s" % (
							indent,
							token,
							type (reference_value)))

				return False, None, None

			if token in reference_value:

				return True, "value", reference_value [token]

			elif str (token) in reference_value:

				return True, "value", reference_value [str (token)]

			else:

				if self.trace:

					uprint (
						"%sToken '%s' not found in %s reference '%s'" % (
							indent,
							token,
							reference_type,
							reference_value))

				return False, None, None

		if self.trace:

			uprint (
				"%svalue not present: %s" % (
					indent,
					token))

		return False, None, None

	def dereference_resource (
			self,
			resource_source,
			token,
			indent):

		resource = (
			self.find_resource (
				resource_source))

		if self.trace:

			uprint (
				"%sdereference_resource (%s, %s)" % (
					indent,
					resource.unique_name,
					token))

		indent = indent + "  "

		for reference \
		in itertools.chain (
			resource.resource_class.references,
			resource.resource_namespace.references,
		):

			if token != reference ["name"]:
				continue

			if reference ["type"] == "resource":

				target_success, target_name = (
					self.resolve_value_real (
						resource,
						reference ["value"],
						indent + "  "))

				if not target_success:
					return False, None, None

				if not target_name in self.resources:
					raise Exception ()

				if "section" in reference:

					target_resource = (
						self.resources [
							target_name])

					target_data = (
						target_resource.get (
							reference ["section"]))

					if self.trace:

						uprint (
							"%sfound resource class section reference: %s" % (
								indent,
								token))

					target_combined_name = ".".join ([
						target_name,
						reference ["section"],
					])

					return True, "resource-section", target_combined_name

				else:

					target_resource = (
						self.find_resource (
							target_name))

					if self.trace:

						uprint (
							"%sfound resource class reference: %s" % (
								indent,
								token))

					return True, "resource", target_resource.unique_name

			elif reference ["type"] == "simple":

				value_success, value = (
					self.resolve_value_real (
						resource,
						reference ["value"],
						indent + "  "))

				if not value_success:

					return False, None, None

				return True, "value", value

			else:

				raise Exception ()

		if resource.has_resolved (token):

			if self.trace:

				uprint (
					"%sfound in resource: %s" % (
						indent,
						token))

			return True, "value", resource.get_resolved (token)

		if token == "parent":

			parent_name = (
				"%s/%s" % (
					resource.resource_class.parent_namespace,
					resource.identity_parent))

			parent = (
				self.resources [
					parent_name])

			if self.trace:

				uprint (
					"%srecurse parent: %s" % (
						indent,
						parent_name))

			return True, "resource", parent_name

		if token in self.all:

			if self.trace:

				uprint (
					"%sfound in globals: %s" % (
						indent,
						token))

			unresolved_value = (
				self.all [token])

			success, resolved_value = (
				self.resolve_value_real (
					resource,
					unresolved_value,
					indent + "  "))

			if success:

				return True, "value", resolved_value

			else:

				return False, None, None

		return False, None, None

	tokenize_re = re.compile ("\s*((?:" + ")|(?:".join ([
		r"$",
		r"[][.,|()]",
		r"==|!=|\+",
		r"[a-zA-Z][a-zA-Z0-9_]*",
		r"'(?:[^'\\]|\\\\|\\\')*'",
	]) + "))")

	def tokenize (self, string):

		ret = []
		position = 0

		while position < len (string):

			match = (
				Inventory.tokenize_re.match (
					string,
					position))

			if not match:
				return False, None

			ret.append (
				match.group (1))

			position = (
				match.end ())

		return True, ret

# ex: noet ts=4 filetype=python
