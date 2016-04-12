from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import with_statement

import os
import subprocess
import sys

try:

	import git
	import yaml

except ImportError:

	pass

import wbs.yamlx as yamlx

def read_index ():

	return yamlx.load_data (
		"third-party/third-party-index")

def pull ():

	third_party_setup = (
		ThirdPartySetup ())

	third_party_setup.load ()
	third_party_setup.pull ()

def build ():

	third_party_setup = (
		ThirdPartySetup ())

	third_party_setup.load ()
	third_party_setup.build ()

class ThirdPartySetup (object):

	def __init__ (self):

		self.project_path = (
			os.path.abspath ("."))

		self.stashed = False

	def load (self):

		self.third_party_index = (
			read_index ())

		self.git_repo = (
			git.Repo (
				"."))

	def pull (self):

		sys.stdout.write (
			"About to pull third party libraries\n")

		try:

			self.create_remotes ()
			self.fetch_remotes ()
			self.stash_changes ()
			self.update_libraries ()

			print (
				"All done")

		finally:

			self.unstash_changes ()

	def build (self):

		sys.stdout.write (
			"About to build third party libraries\n")

		self.build_libraries ()

		print (
			"All done")

	def create_remotes (self):

		remotes_index = dict ([
			(remote.name, remote)
			for remote
			in self.git_repo.remotes
		])

		for library_name, library_data \
		in self.third_party_index.items ():

			if not library_name in remotes_index:

				sys.stdout.write (
					"Create missing remote for %s\n" % (
						library_name))

				remotes_index [library_name] = (
					self.git_repo.create_remote (
						library_name,
						library_data ["url"]))

	def fetch_remotes (self):

		for library_name, library_data \
		in self.third_party_index.items ():

			remote_version = (
				library_data ["version"])

			sys.stdout.write (
				"Fetch remote: %s (%s)\n" % (
					library_name,
					remote_version))

			self.git_repo.remotes [library_name].fetch (
				"%s:refs/%s/%s" % (
					remote_version,
					library_name,
					remote_version))

			sys.stdout.write (
				"\x1b[1A\x1b[K")

		sys.stdout.write (
			"Fetched %s remotes\n" % (
				len (self.third_party_index)))

	def stash_changes (self):

		if self.git_repo.is_dirty ():

			sys.stdout.write (
				"Stashing local changes\n")

			self.git_repo.git.stash (
				"save")

			self.stashed = True

		else:

			self.stashed = False

	def unstash_changes (self):

		if self.stashed:

			sys.stdout.write (
				"Unstashing local changes\n")

			self.git_repo.git.stash (
				"pop")

	def update_libraries (self):

		for library_name, library_data \
		in self.third_party_index.items ():

			library_path = (
				"%s/third-party/%s" % (
					self.project_path,
					library_name))

			library_prefix = (
				"third-party/%s" % (
					library_name))

			if not os.path.isdir (
				library_path):

				sys.stdout.write (
					"First time import library: %s\n" % (
						library_name))

				subprocess.check_call ([
					"git",
					"subtree",
					"add",
					"--prefix",
					library_prefix,
					library_data ["url"],
					library_data ["version"],
					"--squash",
				])

			else:

				local_tree = (
					self.git_repo
						.head
						.commit
						.tree ["third-party"] [library_name])

				git_remote = (
					self.git_repo.remotes [
						library_name])

				if library_data ["version"] in git_remote.refs:

					remote_ref = (
						git_remote.refs [
							library_data ["version"]])

					remote_commit = (
						remote_ref.commit)

				else:

					remote_commit = (
						self.git_repo.commit (
							library_data ["version"]))

				remote_tree = (
					remote_commit.tree)

				if local_tree == remote_tree:
					continue

				sys.stdout.write (
					"Update library: %s\n" % (
						library_name))

				subprocess.check_call ([
					"git",
					"subtree",
					"merge",
					"--prefix", library_prefix,
					unicode (remote_commit),
					"--squash",
					"--message",
					"update %s to %s" % (
						library_name,
						library_data ["version"]),
				])

	def build_libraries (self):

		num_built = 0
		num_failed = 0

		for library_name, library_data \
		in self.third_party_index.items ():

			library_path = (
				"%s/third-party/%s" % (
					self.project_path,
					library_name))

			# ------ work out build

			if "build" in library_data:

				build_data = (
					library_data ["build"])

			elif (

				library_data.get ("auto") == "python"

				and os.path.isfile (
					"%s/setup.py" % library_path)

			):

				build_data = {
					"command": " ".join ([
						"python setup.py build",
					]),
					"environment": {
						"PYTHONPATH":
							"%s/work/lib/python2.7/site-packages" % (
								self.project_path),
					},
				}

				build_data = {
					"command": " ".join ([
						"python setup.py install",
						"--prefix %s/work" % self.project_path,
					]),
					"environment": {
						"PYTHONPATH":
							"%s/work/lib/python2.7/site-packages" % (
								self.project_path),
					},
				}

			else:

				continue

			if isinstance (build_data, unicode):

				build_data = {
					"command": build_data,
				}

			build_data.setdefault (
				"environment",
				{})

			# ---------- perform build

			try:

				sys.stdout.write (
					"Building library: %s\n" % (
						library_name))

				subprocess.check_output (
					build_data ["command"],
					shell = True,
					stderr = subprocess.STDOUT,
					env = dict (
						os.environ, 
						** build_data ["environment"]),
					cwd = library_path)

				sys.stdout.write (
					"\x1b[1A\x1b[K")

				num_built += 1

			except subprocess.CalledProcessError as error:

				sys.stderr.write (
					"Build failed!\n")

				sys.stderr.write (
					error.output)

				num_failed += 1

		if num_failed:

			sys.stdout.write (
				"Built %s remotes with %s failures\n" % (
					num_built,
					num_failed))

		elif num_built:

			sys.stdout.write (
				"Built %s remotes\n" % (
					num_built))

# ex: noet ts=4 filetype=python
