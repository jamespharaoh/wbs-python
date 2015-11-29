from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import with_statement

import git
import os
import subprocess
import yaml

import wbs.yamlx as yamlx

def read_index ():

	return yamlx.load_data (
		"third-party/third-party-index")

def setup ():

	third_party_index = (
		read_index ())

	subprocess.check_call ([
		"git",
		"stash",
	])

	try:

		for project_name, project_data \
		in third_party_index.items ():

			repository = git.Repo (".")

			project_path = (
				"third-party/%s" % (
					project_name))

			if os.path.isdir (
				project_path):

				print (
					"-- update %s --" % (
						project_name))

				subprocess.check_call ([
					"git",
					"subtree",
					"pull",
					"--prefix", project_path,
					project_data ["url"],
					project_data ["version"],
					"--squash",
				])

			else:

				print (
					"-- add %s --" % (
						project_name))

				subprocess.check_call ([
					"git",
					"subtree",
					"add",
					"--prefix", project_path,
					project_data ["url"],
					project_data ["version"],
					"--squash",
				])

	finally:

		subprocess.check_call ([
			"git",
			"stash",
			"pop",
		])

# ex: noet ts=4 filetype=python
