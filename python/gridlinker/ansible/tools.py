from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import collections
import json
import os
import subprocess
import sys

import gridlinker

from wbs import env_resolve

def args (prev_sub_parsers):

	parser = prev_sub_parsers.add_parser (
		"ansible",
		help = "manage or invoke ansible",
		description = """
			The ansible command group contains various commands which can be
			used to hook into ansible directly. Using this tool instead of using
			the ansible binaries directly ensures that the environment is set up
			correctly.
		""")

	next_sub_parsers = parser.add_subparsers ()

	args_playbook (next_sub_parsers)
	args_inventory (next_sub_parsers)

def args_playbook (sub_parsers):

	parser = sub_parsers.add_parser (
		"playbook",
		help = "run an ansible playbook",
		description = """
			This command will execute ansible-playbook directly, passing along
			any arguments unchanged. Remember that you will normally want to
			place a double-dash "--" between the playbook command and the
			arguments which are to be passed to ansible.
		""")

	parser.set_defaults (
		func = do_playbook)

	parser.add_argument (
		"rest",
		nargs = "*",
		help = "arguments to be passed verbatim to ansible-playbook")

def do_playbook (context, args):

	run_playbook (context, args.rest, "exit")

def run_playbook (context, args, action):

	context.ansible_init ()

	with open ("work/ansible.cfg", "w") as file_handle:

		for index, (section_name, section_data) \
		in enumerate (context.ansible_config.items ()):

			if index > 0:
				file_handle.write ("\n")

			file_handle.write ("[%s]\n" % section_name)

			for key, value in section_data.items ():
				file_handle.write ("%s = %s\n" % (key, value))

	result = subprocess.call (
		[
			"%s/bin/ansible-playbook" % context.ansible_home,
		] + context.ansible_args + args,
		env = env_resolve (os.environ, context.env))

	if action == "ignore":

		return

	elif action == "boolean":

		return result == 0

	elif action == "integer":

		return result

	elif action == "exit":

		if result != 0:
			sys.exit (result)

	elif action == "error":

		if result != 0:
			raise Exception (
				"Ansible exited with status %s" % result)

	else:

		raise Exception (
			"Invalid result option: %s" % action)

def args_inventory (sub_parsers):

	parser = sub_parsers.add_parser (
		"inventory",
		help = "run the ansible inventory script",
		description = """
			This command will execute the inventory-script, along with the
			appropriate environment which it needs to work correctly. This is
			useful for debugging.
		""")

	parser.set_defaults (
		func = do_inventory)

	group = (
		parser.add_mutually_exclusive_group (
			required = True))

	group.add_argument (
		"--list",
		action = "store_true",
		help = "list all groups and hosts")

	group.add_argument (
		"--host",
		metavar = "HOST",
		help = "get variables for specific host")

	group.add_argument (
		"--display",
		action = "store_true",
		help = "display all data in friendly form")

	parser.add_argument (
		"--trace",
		action = "store_true",
		help = "enable trace mode to debug inventory")

def do_inventory (context, args):

	if args.trace:
		context.trace = True

	if args.list:
		do_inventory_list (context)

	elif args.host:
		do_inventory_host (context, args.host)

	elif args.display:
		do_inventory_display (context)

	else:
		raise Exception ()

def do_inventory_list (context):

	inventory = context.inventory

	output = {
		"_meta": {
			"hostvars": {},
		},
	}

	output ["all"] = {
		"vars": inventory.all,
	}

	for class_name, class_data \
	in inventory.classes.items ():

		output [class_name] = {
			"children": inventory.group_children [class_name],
			"hosts": inventory.group_members [class_name],
		}

	for group_name, group_data in inventory.groups.items ():

		output [group_name] = {
			"vars": group_data,
			"hosts": inventory.group_members [group_name],
		}

	for resource_name, resource \
	in inventory.resources.items ():

		output ["_meta"] ["hostvars"] [resource_name] = (
			resource.combined ())

	if not "localhost" in output ["_meta"] ["hostvars"]:

		output ["_meta"] ["hostvars"] ["localhost"] = {
			"ansible_connection": "local",
		}

	for key, value \
	in context.project_metadata ["project_data"].items ():

		output ["all"] ["vars"] [key] = (
			context.local_data [value])

	resolve_resource_data (
		context,
		output)

	output ["localhost"] = {
		"ansible_connection": "local",
	}

	for group_name \
	in inventory.class_groups:

		output [group_name] = {
			"hosts": sorted (
				inventory.group_members [group_name]),
		}

	output ["all"] ["vars"] ["namespaces"] = dict ([
		(namespace.name (), [
			resource.name ()
			for resource
			in namespace.resources()
		])
		for namespace in inventory.namespaces.values ()
	])

	output ["all"] ["vars"] ["classes"] = dict ([
		(class_data.name (), [
			resource.name ()
			for resource
			in class_data.resources ()
		])
		for class_data \
		in inventory.classes.values ()
	])

	output ["all"] ["vars"] ["resources"] = dict ([
		(resource_name, resource._raw_data ["identity"])
		for resource_name, resource
		in inventory.resources.items ()
	])

	print_json (output)

def resolve_resource_data (context, output):

	inventory = context.inventory

	for resource_data_key, resource_data_value \
	in context.project_metadata ["resource_data"].items ():

		if resource_data_key in output ["all"] ["vars"]:

			raise Exception (
				"Global key %s in globals and project resource data" % (
					resource_data_key))

		# find resources

		if resource_data_value ["group"] in inventory.group_members:

			resources = map (
				lambda resource_name:
					inventory.resources [resource_name],
				inventory.group_members [resource_data_value ["group"]])

		elif resource_data_value ["group"] in inventory.namespaces:

			resources = map (
				lambda resource:
					inventory.resources [resource.name ()],
				inventory.namespaces [
					resource_data_value ["group"]
				].resources ())

		else:

			raise Exception ("".join ([
				"Invalid group or namespace '%s' " % (
					resource_data_value ["group"]),
				"referenced in resource_data for '%s'" % (
					resource_data_key),
			]))

		# resolve section

		if "section" in resource_data_value:

			entries = [
				(
					inventory.resolve_value_or_fail (
						resource,
						resource_data_value ["key"]),
					resource.get (
						resource_data_value ["section"]),
				)
				for resource in resources
			]

		else:

			entries = [
				(
					inventory.resolve_value_or_fail (
						resource,
						resource_data_value ["key"]),
					resource.combined (),
				)
				for resource in resources
			]

		# sort by key

		entries.sort (
			key = lambda entry: entry [0])

		# store data

		resource_data_dict = (
			collections.OrderedDict ())

		output ["all"] ["vars"] [resource_data_key] = (
			resource_data_dict)

		for entry_key, entry_value in entries:

			if entry_key == "":
				continue

			if resource_data_value.get ("format") == "list":

				resource_data_dict.setdefault (
					entry_key,
					list ())

				resource_data_dict [entry_key].append (
					entry_value)

			else:

				if entry_key in resource_data_dict:

					raise Exception (
						"Duplicated key '%s' in resource data '%s'" % (
							entry_key,
							resource_data_key))

				resource_data_dict [entry_key] = (
					entry_value)

def do_inventory_host (context, host_name):

	raise Exception ("TODO")

def do_inventory_display (context):

	raise Exception ("TODO")

def print_json (data):

	print (
		json.dumps (
			data,
			sort_keys = True,
			indent = 4,
			separators = (", ", ": ")))

# ex: noet ts=4 filetype=python
