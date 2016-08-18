from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib

def file_contents (filename):

	with open (filename) \
	as file_handle:

		return file_handle.read ()

def hash_sha1 (data):

	hasher = (
		hashlib.sha1 (
			data))

	return hasher.hexdigest ()

def file_hash_sha1 (filename):

	return hash_sha1 (
		file_contents (
				filename))

# ex: noet ts=4 filetype=python
