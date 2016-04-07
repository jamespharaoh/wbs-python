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

def setup ():

	third_party_setup = (
		ThirdPartySetup ())

	third_party_setup.setup ()

class ThirdPartySetup (object):

	def __init__ (self):

		self.stashed = False

	def setup (self):

		self.third_party_index = (
			read_index ())

		self.git_repo = (
			git.Repo (
				"."))

		sys.stdout.write (
			"About to set up third party libraries\n")

		try:

			self.create_remotes ()
			self.fetch_remotes ()
			self.stash_changes ()
			self.update_libraries ()
			self.build_libraries ()

			print (
				"All done")

		finally:

			self.unstash_changes ()

	def create_remotes (self):

		remotes_index = dict ([
			(remote.name, remote)
			for remote
			in self.git_repo.remotes
		])

		for project_name, project_data \
		in self.third_party_index.items ():

			if not project_name in remotes_index:

				sys.stdout.write (
					"Create missing remote for %s\n" % (
						project_name))

				remotes_index [project_name] = (
					self.git_repo.create_remote (
						project_name,
						project_data ["url"]))

	def fetch_remotes (self):

		for project_name, project_data \
		in self.third_party_index.items ():

			remote_version = (
				project_data ["version"])

			sys.stdout.write (
				"Fetch remote: %s (%s)\n" % (
					project_name,
					remote_version))

			self.git_repo.remotes [project_name].fetch (
				"%s:refs/%s/%s" % (
					remote_version,
					project_name,
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

		for project_name, project_data \
		in self.third_party_index.items ():

			project_path = (
				"third-party/%s" % (
					project_name))

			if not os.path.isdir (
				project_path):

				sys.stdout.write (
					"First time import library: %s\n" % (
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

			else:

				local_tree = (
					self.git_repo
						.head
						.commit
						.tree ["third-party"] [project_name])

				git_remote = (
					self.git_repo.remotes [
						project_name])

				if project_data ["version"] in git_remote.refs:

					remote_ref = (
						git_remote.refs [
							project_data ["version"]])

					remote_commit = (
						remote_ref.commit)

				else:

					remote_commit = (
						self.git_repo.commit (
							project_data ["version"]))

				remote_tree = (
					remote_commit.tree)

				if local_tree == remote_tree:
					continue

				sys.stdout.write (
					"Update library: %s\n" % (
						project_name))

				subprocess.check_call ([
					"git",
					"subtree",
					"merge",
					"--prefix",
					project_path,
					unicode (remote_commit),
					"--squash",
					"--message",
					"update %s to %s" % (
						project_name,
						project_data ["version"]),
				])

	def build_libraries (self):

		num_built = 0
		num_failed = 0

		for project_name, project_data \
		in self.third_party_index.items ():

			if not "build" in project_data:
				continue

			project_path = (
				"third-party/%s" % (
					project_name))

			build_data = (
				project_data ["build"])

			if isinstance (build_data, unicode):

				build_data = {
					"command": build_data,
				}

			build_data.setdefault (
				"environment",
				{})

			try:

				sys.stdout.write (
					"Building library: %s\n" % (
						project_name))

				build_output = (
					subprocess.check_output (
						build_data ["command"],
						shell = True,
						stderr = subprocess.STDOUT,
						cwd = project_path))

				sys.stdout.write (
					"\x1b[1A\x1b[K")

				num_built += 1

			except:

				sys.stderr.write (
					"Build failed!\n")

				sys.stderr.write (
					build_output)

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
