from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

current_status = None
temporary_status = True

class WithStatus (object):

	def __enter__ (self):

		pass

	def __exit__ (self, exception_type, exception_value, traceback):

		if exception_value:

			keep_status ()

		else:

			clear_status ()

def status (value):

	if "\n" in value:
		raise Exception ()

	global current_status

	if current_status:
		raise Exception ()

	current_status = value

	sys.stderr.write (
		"%s ...\n" % current_status)

	return WithStatus ()

def keep_status ():

	global current_status

	if not current_status:
		raise Exception ()

	current_status = None

def clear_status ():

	global current_status

	if not current_status:
		return

	if temporary_status:

		sys.stderr.write (
			"\x1b[1A\x1b[K")

	current_status = None

def notice (value):

	if "\n" in value:
		raise Exception ()

	if current_status and temporary_status:

		sys.stderr.write (
			"\x1b[1A\x1b[K")

	sys.stderr.write (
		"%s\n" % value)

	if current_status and temporary_status:

		sys.stderr.write (
			"%s\n" % current_status)

def output (value):

	if len (value) and value [-1] != "\n":
		raise Exception ()

	if current_status and temporary_status:

		sys.stderr.write (
			"\x1b[1A\x1b[K")

	sys.stderr.write (
		value)

	if current_status and temporary_status:

		sys.stderr.write (
			"%s\n" % current_status)

# ex: noet ts=4 filetype=pyton
