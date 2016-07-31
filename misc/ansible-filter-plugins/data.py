from __future__ import absolute_import
from __future__ import unicode_literals

import collections
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

def order_by_depends (
		items,
		name_function = None,
		depends_function = None):

	if isinstance (items, dict):

		if not name_function:

			name_function = (
				lambda (key, value):
					key)

		if not depends_function:

			depends_function = (
				lambda (key, value):
					value.get ("depends", []))

		items = items.items ()

		return_function = (
			lambda items:
				collections.OrderedDict (
					items))

	else:

		if not name_function:

			name_function = (
				lambda item:
					item ["name"])

		if not depends_function:

			depends_function = (
				lambda item:
					item.get ("depends", []))

		return_function = (
			lambda items:
				items)

	# sanity check

	all_names = set ([
		name_function (item)
		for item in items
	])

	all_depends = set ([
		depends
		for item in items
		for depends in depends_function (item)
	])

	missing_depends = (
		all_depends - all_names)

	if missing_depends:

		raise Exception (
			"Missing dependencies: %s" % (
				", ".join (missing_depends)))

	# sort by dependencies

	unordered_items = (
		list (items))

	ordered_items = (
		list ())

	satisfied_items = (
		set ())

	while unordered_items:

		progress = False

		next_unordered_items = (
			list ())

		for item in unordered_items:

			item_depends = (
				depends_function (
					item))

			item_name = (
				name_function (
					item))

			if set (item_depends) - satisfied_items:

				next_unordered_items.append (
					item)

			else:

				ordered_items.append (
					item)

				satisfied_items.add (
					item_name)

				progress = True

		if not progress:

			raise Exception (
				"Circular dependency between: %s" % (
					", ".join ([
						name_function (item)
						for item
						in unordered_items
					])))

		unordered_items = (
			next_unordered_items)

	return return_function (
		ordered_items)

class FilterModule (object):

	def filters (self):

		return {

			"flatten_hash": flatten_hash,
			"list_to_map": list_to_map,
			"dict_map": dict_map,
			"order_by_depends": order_by_depends,

	}

# ex: noet ts=4 filetype=python
