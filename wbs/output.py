from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

__all__ = [

	"ConsoleLog",
	"WithStatus",

	"log",
	"uprint",

]

class ConsoleLog (object):

	def __init__ (
			self,
			stream = sys.stderr,
			temporary_status = True):

		self.current_status = None
		self.stream = stream
		self.temporary_status = temporary_status

	def status (self, value):

		if "\n" in value:

			raise Exception (
				"Status contains newline")

		if self.current_status:

			raise Exception (
				"Status set without being cleared")

		self.current_status = value

		self.write (
			"%s ...\n" % self.current_status)

		return WithStatus ()

	def keep_status (self):

		if not self.current_status:
			raise Exception ()

		self.current_status = None

	def clear_status (self):

		if not self.current_status:
			return

		if self.temporary_status:

			self.write (
				"\x1b[1A\x1b[K")

		self.current_status = None

	def notice (self, value):

		if "\n" in value:
			raise Exception ()

		if self.current_status \
		and self.temporary_status:

			self.write (
				"\x1b[1A\x1b[K")

		self.write (
			"%s\n" % value)

		if self.current_status \
		and self.temporary_status:

			self.write (
				"%s\n" % self.current_status)

	def output (self, value):

		if len (value) and value [-1] != "\n":
			raise Exception ()

		if self.current_status \
		and self.temporary_status:

			self.write (
				"\x1b[1A\x1b[K")

		self.write (
			value)

		if self.current_status \
		and self.temporary_status:

			self.write (
				"%s\n" % self.current_status)

	def write (self, message):

		self.stream.write (
			message.encode ("utf-8"))

class WithStatus (object):

	def __init (self, log):

		self.log = log

	def __enter__ (self):

		pass

	def __exit__ (self, exception_type, exception_value, traceback):

		if exception_value:

			log.keep_status ()

		else:

			log.clear_status ()

log = ConsoleLog ()

def uprint (message):

	print (message.encode ("utf-8"))

# ex: noet ts=4 filetype=pyton
