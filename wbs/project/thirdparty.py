from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import with_statement

import os
import signal
import subprocess
import sys

try:

	import git
	import yaml

except ImportError:

	pass

import wbs.yamlx as yamlx
import wbs.output as output

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

def merge ():

	third_party_setup = (
		ThirdPartySetup ())

	third_party_setup.load ()
	third_party_setup.merge ()

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

		output.notice (
			"About to pull third party libraries")

		try:

			self.create_remotes ()
			self.fetch_remotes ()
			self.stash_changes ()
			self.update_libraries ()

			output.notice (
				"All done")

		except KeyboardInterrupt:

			output.notice (
				"Aborting due to user request")

		finally:

			self.unstash_changes ()

	def build (self):

		output.notice (
			"About to build third party libraries")

		try:

			self.stash_changes ()
			self.build_libraries ()

			output.notice (
				"All done")

		except KeyboardInterrupt:

			output.notice (
				"Aborting due to user request")

		finally:

			self.unstash_changes ()

	def merge (self):

		output.notice (
			"About to merge third party libraries")

		try:

			self.stash_changes ()
			self.merge_libraries ()

			output.notice (
				"All done")

		except KeyboardInterrupt:

			output.notice (
				"Aborting due to user request")

		finally:

			self.unstash_changes ()

	def create_remotes (self):

		remotes_index = dict ([
			(remote.name, remote)
			for remote
			in self.git_repo.remotes
		])

		for library_name, library_data \
		in self.third_party_index.items ():

			if not library_name in remotes_index:

				output.status (
					"Create missing remote for %s" % (
						library_name))

				remotes_index [library_name] = (
					self.git_repo.create_remote (
						library_name,
						library_data ["url"]))

	def fetch_remotes (self):

		for library_name, library_data \
		in self.third_party_index.items ():

			if "version" in library_data:

				with output.status (
					"Fetch remote: %s (%s)" % (
						library_name,
						library_data ["version"])):

					self.git_repo.remotes [library_name].fetch (
						"refs/tags/%s:refs/remotes/%s/%s" % (
							library_data ["version"],
							library_name,
							library_data ["version"]))

			elif "branch" in library_data:

				with sys.stdout.write (
					"Fetch remote: %s (%s)\n" % (
						library_name,
						library_data ["branch"])):

					self.git_repo.remotes [library_name].fetch (
						"%s:refs/%s/%s" % (
							library_data ["branch"],
							library_name,
							library_data ["branch"]))

			else:

				raise Exception ()

		output.notice (
			"Fetched %s remotes" % (
				len (self.third_party_index)))

	def handle_interrupt (self, * arguments):

		output.notice (
			"Aborting...")

		self.interrupted = True

	def stash_changes (self):

		if self.stashed:
			return

		self.interrupted = False

		saved_signal = (
			signal.signal (
				signal.SIGINT,
				self.handle_interrupt))

		output.notice (
			"Stashing local changes")

		self.stashed_head_tree = (
			self.git_repo.head.commit.tree)

		self.stashed_index_tree = (
			self.git_repo.index.write_tree ())

		self.git_repo.index.add (
			[ "third-party" ],
			force = False)

		self.stashed_working_tree = (
			self.git_repo.index.write_tree ())

		self.git_repo.index.reset (
			working_tree = True)

		self.stashed = True

		signal.signal (
			signal.SIGINT,
			saved_signal)

		if self.interrupted:
			raise KeyboardInterrupt ()

	def unstash_changes (self):

		if not self.stashed:
			return

		output.notice (
			"Unstashing local changes")

		merged_working_index = (
			git.IndexFile.from_tree (
				self.git_repo,
				self.stashed_head_tree,
				self.stashed_working_tree,
				self.git_repo.head.commit.tree))

		self.git_repo.index.reset (
			merged_working_index.write_tree (),
			working_tree = True)

		merged_index = (
			git.IndexFile.from_tree (
				self.git_repo,
				self.stashed_head_tree,
				self.stashed_index_tree,
				self.git_repo.head.commit.tree))

		self.git_repo.index.reset (
			merged_index.write_tree ())

		self.stashed = False

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

				output.notice (
					"First time import library: %s" % (
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

				if "version" in library_data:

					remote_ref = (
						git_remote.refs [
							library_data ["version"]])

					remote_commit = (
						remote_ref.commit)

				elif "branch" in library_data:

					remote_ref = (
						git_remote.refs [
							library_data ["branch"]])

					remote_commit = (
						remote_ref.commit)

				remote_tree = (
					remote_commit.tree)

				if local_tree == remote_tree:
					continue

				with output.status (
					"Update library: %s" % (
						library_name)):

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

				with output.status (
					"Building library: %s" % (
						library_name)):

					subprocess.check_output (
						build_data ["command"],
						shell = True,
						stderr = subprocess.STDOUT,
						env = dict (
							os.environ,
							** build_data ["environment"]),
						cwd = library_path)

				num_built += 1

			except subprocess.CalledProcessError as error:

				output.notice (
					"Build failed!")

				output.output (
					error.output)

				num_failed += 1

		if num_failed:

			output.notice (
				"Built %s remotes with %s failures" % (
					num_built,
					num_failed))

		elif num_built:

			output.notice (
				"Built %s remotes" % (
					num_built))

	def merge_libraries (self):

		num_merged = 0
		num_failed = 0

		for library_name, library_data \
		in self.third_party_index.items ():

			if not "merge" in library_data:
				continue

			library_path = (
				"%s/third-party/%s" % (
					self.project_path,
					library_name))

			try:

				for library_merge in library_data ["merge"]:

					with output.status (
						"Merging library: %s (%s -> %s)" % (
							library_name,
							library_merge ["source"],
							library_merge ["target"])):

						unmerged_path = (
							".merged/%s" % (
								library_merge ["target"]))

						if os.path.exists (
							"%s/%s" % (
								self.project_path,
								unmerged_path)):

							unmerged_tree = (
								self.git_repo.head.commit.tree [
									unmerged_path])

						else:

							unmerged_tree = (
								self.git_repo.tree (
									"4b825dc642cb6eb9a060e54bf8d69288fbee4904"))

						target_path = (
							"%s" % (
								library_merge ["target"] [1:]))

						if os.path.exists (
							"%s/%s" % (
								self.project_path,
								target_path)):

							target_tree = (
								self.git_repo.head.commit.tree [
									target_path])

						else:

							target_tree = (
								self.git_repo.tree (
									"4b825dc642cb6eb9a060e54bf8d69288fbee4904"))

						source_path = (
							"third-party/%s%s" % (
								library_name,
								library_merge ["source"]))

						source_tree = (
							self.git_repo.head.commit.tree [
								source_path])

						merged_index = (
							git.IndexFile.from_tree (
								self.git_repo,
								unmerged_tree,
								target_tree,
								source_tree))

						merged_tree = (
							merged_index.write_tree ())

						output.notice (
							"MERGED TREE: " + unicode (merged_tree))

						if os.path.exists (
							"%s/%s" % (
								self.project_path,
								target_path)):

							self.git_repo.git.rm (
								"--force",
								"-r",
								target_path)

						self.git_repo.git.read_tree (
							unicode (merged_tree),
							"--prefix",
							target_path)

						self.git_repo.git.read_tree (
							unicode (source_tree),
							"--prefix",
							unmerged_path)

						output.notice (
							"INDEX TREE: " + unicode (
								self.git_repo.index.write_tree ()))

				self.git_repo.index.commit (
					"Auto-merge changes from %s" % (
						library_name))

				num_merged += 1

			except subprocess.CalledProcessError as error:

				output.notice (
					"Merge failed!")

				output.output (
					error.output)

				num_failed += 1

		if num_failed:

			output.notice (
				"Merged %s libraries with %s failures" % (
					num_merged,
					num_failed))

		elif num_merged:

			output.notice (
				"Merged %s libraries" % (
					num_merged))

# ex: noet ts=4 filetype=python
