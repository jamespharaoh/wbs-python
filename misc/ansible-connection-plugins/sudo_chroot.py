from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__metaclass__ = type

import distutils.spawn
import os
import subprocess

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.connection import ConnectionBase
from ansible.module_utils.basic import is_executable
from ansible.utils.unicode import to_bytes

try:

	from __main__ import display

except ImportError:

	from ansible.utils.display import Display
	display = Display ()

class Connection (ConnectionBase):

	transport = "chroot"
	has_pipelining = True
	become_methods = C.BECOME_METHODS

	def __init__ (
			self,
			play_context,
			new_stdin,
			* arguments,
			** keyword_arguments):

		super (Connection, self).__init__ (
			play_context,
			new_stdin,
			* arguments,
			** keyword_arguments)

		self.chroot = (
			self._play_context.remote_addr)

		self.sudo_command = (
			distutils.spawn.find_executable (
				"sudo"))

		if not self.sudo_command:

			raise errors.AnsibleError (
				"sudo command not found in PATH")

		self.chroot_command = (
			distutils.spawn.find_executable (
				"chroot"))

		if not self.chroot_command \
		and os.path.isfile ("/usr/sbin/chroot"):

			self.chroot_command = (
				"/usr/sbin/chroot")

		if not self.chroot_command:

			raise errors.AnsibleError (
				"chroot command not found in PATH")

	def _connect (self):

		super (Connection, self)._connect ()

		if not self._connected:

			display.vvv ("THIS IS A LOCAL CHROOT DIR", host = self.chroot)

			self._connected = True

	def _buffered_exec_command (
			self,
			command,
			stdin = subprocess.PIPE):

		if C.DEFAULT_EXECUTABLE:

			executable = (
				C.DEFAULT_EXECUTABLE.split () [0])

		else:

			executable = (
				"/bin/sh")

		local_command = [
			self.sudo_command,
			self.chroot_command,
			self.chroot,
			executable,
			"-c",
			command,
		]

		display.vvv (
			"EXEC %s" % (
				local_command),
			host = self.chroot)

		process = (
			subprocess.Popen (
				local_command,
				shell = False,
				stdin = stdin,
				stdout = subprocess.PIPE,
				stderr = subprocess.PIPE))

		return process

	def exec_command (
			self,
			command,
			in_data = None,
			sudoable = False):

		super (Connection, self).exec_command (
			command,
			in_data = in_data,
			sudoable = sudoable)

		process = (
			self._buffered_exec_command (
				command))

		stdout, stderr = (
			process.communicate (
				in_data))

		return (
			process.returncode,
			stdout,
			stderr)

	def put_file (self, in_path, out_path):

		if not out_path.startswith (os.path.sep):

			out_path = (
				os.path.join (
					os.path.sep, out_path))

		normpath = (
			os.path.normpath (
				out_path))

		out_path = (
			os.path.join (
				self.chroot,
				normpath [1:]))

		display.vvv (
			"PUT %s TO %s" % (
				in_path,
				out_path),
			host = self.chroot)

		if not os.path.exists (in_path):

			raise errors.AnsibleFileNotFound (
				"file or module does not exist: %s" % in_path)

		try:

			subprocess.check_call ([
				self.sudo_command,
				"cp",
				in_path,
				out_path,
			])

		except Exception:

			traceback.print_exc ()

			raise errors.AnsibleError (
				"failed to copy %s to %s" % (
					in_path,
					out_path))

	def fetch_file (self, in_path, out_path):

		if not in_path.startswith (os.path.sep):

			in_path = (
				os.path.join (
					os.path.sep,
					in_path))

		normpath = (
			os.path.normpath (
				in_path))

		in_path = (
			os.path.join (
				self.chroot,
				normpath [1:]))

		display.vvv (
			"FETCH %s TO %s" % (
				in_path,
				out_path),
			host = self.chroot)

		raise Exception ("TODO")

	def close (self):

		super (Connection, self).close ()

		self._connected = False

# ex: noet ts=4 filetype=python
