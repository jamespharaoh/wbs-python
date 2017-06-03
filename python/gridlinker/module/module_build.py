from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from wbs import yamlx

__all__ = [
	"build_modules",
]

def build_modules (
		home,
		module_names = None):

	all_modules = (
		load_modules (
			home))

	for module in all_modules.values ():

		if module_names \
		and module.module_name () not in module_names:

			continue

		print (
			"===== Building %s =====" % (
				module.module_name ()))

		module.build ()

class GridlinkerModule (object):

	__slots__ = [

		"_home",

		"_module_group_name",
		"_module_name",
		"_module_path",
		"_module_data",

	]

	def __init__ (
			self,
			home,
			module_group_name,
			module_name,
			module_path,
			module_data):

		self._home = home

		self._module_group_name = module_group_name
		self._module_name = module_name
		self._module_path = module_path
		self._module_data = module_data

	# accessors

	def module_name (self):

		return self._module_name

	# implementation

	def build (self):

		directory_builder = (
			DirectoryBuilder (
				self._home,
				"roles/%s" % (
					self._module_name)))

		self.build_main (
			directory_builder)

		self.build_common (
			directory_builder,
			self._module_data ["common"])

		for task_data \
		in self._module_data ["tasks"]:

			self.build_task (
				directory_builder,
				task_data)

	def build_main (
			self,
			directory_builder):

		main_directory_builder = (
			directory_builder.subdirectory (
				self._module_name))

		main_meta_directory_builder = (
			main_directory_builder.subdirectory (
				"meta"))

		main_meta_directory_builder.create_yaml_file (
			"main.yml",
			{
				"dependencies": [
					"%s-common" % self._module_name,
				] + [
					"%s-%s" % (
						self._module_name,
						task ["name"])
					for task
					in self._module_data ["tasks"]
				],
			})

	def build_common (
			self,
			directory_builder,
			common_data):

		common_directory_builder = (
			directory_builder.subdirectory (
				"%s-common" % (
					self._module_name)))

		common_defaults_directory_builder = (
			common_directory_builder.subdirectory (
				"defaults"))

		common_defaults_directory_builder.create_yaml_file (
			"main.yml",
			common_data)

	def build_task (
			self,
			directory_builder,
			task_data):

		task_directory_builder = (
			directory_builder.subdirectory (
				"%s-%s" % (
					self._module_name,
					task_data ["name"])))

		if task_data ["name"] != "common":

			self.build_task_meta (
				task_directory_builder,
				task_data)

		self.build_task_tasks (
			task_directory_builder,
			task_data)

		task_directory_builder.create_link (
			"templates",
			"../../../modules/%s/%s/templates" % (
				self._module_group_name,
				self._module_name))

		task_directory_builder.create_link (
			"files",
			"../../../modules/%s/%s/files" % (
				self._module_group_name,
				self._module_name))

	def build_task_meta (
			self,
			task_directory_builder,
			task_data):

		task_meta_directory_builder = (
			task_directory_builder.subdirectory (
				"meta"))

		task_meta_directory_builder.create_yaml_file (
			"main.yml",
			{
				"dependencies": [
					"%s-common" % self._module_name,
				],
			})

	def build_task_tasks (
			self,
			task_directory_builder,
			task_data):

		task_tasks_directory_builder = (
			task_directory_builder.subdirectory (
				"tasks"))

		task_tasks_directory_builder.create_yaml_file (
			"main.yml",
			[
				{
					"include": "%s-%s.yml" % (
						self._module_name,
						task_data ["name"]),
					"tags": task_data ["tags"],
					"when": "(%s)" % ") and (".join (
						task_data.get (
							"when",
							[ "True" ])),
				},
			])

		task_tasks_directory_builder.create_link (
			"%s-%s.yml" % (
				self._module_name,
				task_data ["name"]),
			"../../../../modules/%s/%s/tasks/%s-%s.yml" % (
				self._module_group_name,
				self._module_name,
				self._module_name,
				task_data ["name"]))

class DirectoryBuilder (object):

	__slots__ = [
		"_parent",
		"_name",
		"_files",
	]

	def __init__ (self, parent, name):

		self._parent = parent
		self._name = name
		self._files = set ()

		path = "%s/%s" % (
			self._parent,
			self._name)

		if not os.path.isdir (path):

			print (
				"Creating directory %s" % (
					name))

			os.mkdir (
				path)

	def subdirectory (self, name):

		self._files.add (
			name)

		self.create_directory (
			name)

		return SubDirectoryBuilder (
			self,
			name)

	def create_directory (self, name):

		self._files.add (
			name)

		path = (
			"%s/%s/%s" % (
				self._parent,
				self._name,
				name))

		if not os.path.isdir (path):

			print (
				"Creating directory %s" % (
					"%s/%s" % (
						self._name,
						name)))

			os.mkdir (
				path)

		return path

	def create_yaml_file (self, name, data, schema = None):

		content = (
			yamlx.encode (
				schema,
				data))

		return self.create_file (
			name,
			content.strip ().split ("\n"))

	def create_link (self, name, new_target):

		self._files.add (
			name)

		path = (
			"%s/%s/%s" % (
				self._parent,
				self._name,
				name))

		if not os.path.islink (path):

			print (
				"Creating link %s/%s" % (
					self._name,
					name))

			os.symlink (
				new_target,
				path)

		else:

			old_target = (
				os.readlink (
					path))

			if old_target != new_target:

				print (
					"Updating link %s/%s" % (
						self._name,
						name))

				os.unlink (
					path)

				os.symlink (
					new_target,
					path)

	def create_file (self, name, content_lines):

		self._files.add (
			name)

		path = (
			"%s/%s/%s" % (
				self._parent,
				self._name,
				name))

		new_content = (
			"\n".join (content_lines) + "\n")

		if not os.path.isfile (path):

			print (
				"Creating file %s/%s" % (
					self._name,
					name))

			with open (path, "w") as file_handle:

				file_handle.write (
					new_content)

		else:

			with open (path, "r") as file_handle:

				old_content = (
					file_handle.read ())

			if new_content != old_content:

				print (
					"Updating file %s/%s" % (
						self._name,
						name))

				with open (path, "w") as file_handle:

					file_handle.write (
						new_content)

class SubDirectoryBuilder (object):

	__slots__ = [
		"_parent",
		"_name",
	]

	def __init__ (self, parent, name):

		self._parent = parent
		self._name = name

	def subdirectory (self, name):

		return self._parent.subdirectory (
			"%s/%s" % (
				self._name,
				name))

	def create_directory (self, name):

		return self._parent.create_directory (
			"%s/%s" % (
				self._name,
				name))

	def create_yaml_file (self, name, data, schema = None):

		return self._parent.create_yaml_file (
			"%s/%s" % (
				self._name,
				name),
			data,
			schema)

	def create_link (self, name, new_target):

		return self._parent.create_link (
			"%s/%s" % (
				self._name,
				name),
			new_target)

	def create_file (self, name, content_lines):

		return self._parent.create_file (
			"%s/%s" % (
				self._name,
				name),
			content_lines)

def load_modules (
		home):

	modules = dict ()

	for module_group_name \
	in os.listdir ("%s/modules" % home):

		module_group_path = (
			"%s/modules/%s" % (
				home,
				module_group_name))

		for module_name \
		in os.listdir (module_group_path):

			if module_name in modules:

				raise Exception ()

			module_path = (
				"%s/%s" % (
					module_group_path,
					module_name))

			module_data = (
				yamlx.load_data (
					"%s/%s-module" % (
						module_path,
						module_name)))

			modules [module_name] = (
				GridlinkerModule (
					home,
					module_group_name,
					module_name,
					module_path,
					module_data))

	return modules

# ex: noet ts=4 filetype=python
