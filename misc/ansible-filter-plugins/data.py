from __future__ import absolute_import
from __future__ import unicode_literals

import itertools

def flatten_hash (values, * inner_names):

	ret = []

	for outer_key, outer_value in values.items ():

		for inner_items in itertools.product (* [
			outer_value [inner_name]
			for inner_name in inner_names
		]):

			item = {
				"outer": {
					"key": outer_key,
					"value": outer_value,
				},
			}

			for index, inner_name in enumerate (inner_names):

				inner_item = inner_items [index]
				inner_collection = outer_value [inner_name]

				if isinstance (inner_collection, list):

					item [inner_name] = inner_item

				if isinstance (inner_collection, dict):

					item [inner_name] = {
						"key": inner_item,
						"value": inner_collection [inner_item],
					}

				ret.append (item)

		return ret

def property_get (value, path):

	if "." in path:

		first, rest = path.split (".", 1)
		return property_get (value [first], rest)

	else:

		return value [path]

def list_to_map (items, key_name, value_name):

	return dict ([
		(property_get (item, key_name), property_get (item, value_name))
		for item in items
	])

def dict_map (keys, mapping):

	return list ([
		mapping [key]
		for key in keys
	])

def order_by_depends (projects):

	# sanity check

	all_project_names = set ([
		project ["name"]
		for project in projects
	])

	all_depends = set ([
		depends
		for project in projects
		for depends in project.get ("depends", [])
	])

	missing_depends = (
		all_depends - all_project_names)

	if missing_depends:

		raise Exception (
			"Missing dependent projects: %s" % (
				", ".join (missing_depends)))

	# sort by dependencies

	unordered_projects = (
		list (projects))

	ordered_projects = (
		list ())

	satisfied_projects = (
		set ())

	while unordered_projects:

		progress = False

		next_unordered_projects = (
			list ())

		for project in unordered_projects:

			if set (project.get ("depends", [])) \
				- satisfied_projects:

				next_unordered_projects.append (
					project)

			else:

				ordered_projects.append (
					project)

				satisfied_projects.add (
					project ["name"])

				progress = True

		if not progress:

			raise Exception (
				"Circular dependency between: %s" % (
					", ".join ([
						project ["name"]
						for project
						in unordered_projects
					])))

		unordered_projects = (
			next_unordered_projects)

	return ordered_projects

class FilterModule (object):

	def filters (self):

		return {

			"flatten_hash": flatten_hash,
			"list_to_map": list_to_map,
			"dict_map": dict_map,
			"order_by_depends": order_by_depends,

	}

# ex: noet ts=4 filetype=python
