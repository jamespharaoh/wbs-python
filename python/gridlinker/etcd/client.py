from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import collections
import httplib
import itertools
import json
import os
import random
import re
import ssl
import threading
import time
import urllib
import wbs

from wbs import log
from wbs import uprint
from wbs import yamlx

__all__ = [
	"EtcdClient",
	"args",
]

class EtcdClient:

	__slots__ = [

		"servers",
		"port",
		"secure",
		"client_ca_cert",
		"client_cert",
		"client_key",
		"prefix",
		"cache_path",

		"connection",
		"pid",
		"modified_index",
		"cache_metadata",
		"watch_thread",

	]

	def __init__ (
		self,
		servers = [ "localhost" ],
		port = 2379,
		secure = False,
		client_ca_cert = None,
		client_cert = None,
		client_key = None,
		prefix = "",
		cache_path = None,
	):

		self.servers = servers
		self.port = port
		self.secure = secure
		self.client_ca_cert = client_ca_cert
		self.client_cert = client_cert
		self.client_key = client_key
		self.prefix = prefix
		self.cache_path = cache_path

		self.connection = threading.local ()
		self.connection.value = None
		self.connection.ssl_context = None
		self.connection.servers = list (self.servers)

		self.pid = None

		random.shuffle (self.connection.servers)

		if self.secure:

			self.connection.server_url = (
				"https://%s:%s" % (
					self.connection.servers [0],
					self.port))

			if hasattr (ssl, "SSLContext"):

				self.connection.ssl_context = ssl.SSLContext (
					ssl.PROTOCOL_TLSv1_2)

				self.connection.ssl_context.verify_mode = ssl.CERT_REQUIRED
				self.connection.ssl_context.check_hostname = False

				self.connection.ssl_context.load_verify_locations (
					cafile = self.client_ca_cert)

			else:

				self.connection.ssl_context = None

		else:

			self.connection.server_url = (
				"http://%s:%s" % (
					self.connection.servers [0],
					self.port))

		if self.cache_path:

			self.init_cache ()

	def init_cache (self):

		if not os.path.exists (
			self.cache_path):

			os.mkdir (
				self.cache_path)

		if os.path.exists (
			"%s/metadata" % self.cache_path):

			self.cache_metadata = (
				yamlx.load_data (
					"%s/metadata" % self.cache_path))

			self.modified_index = int (
				self.cache_metadata ["modified-index"])

		else:

			with log.status (
				"Priming etcd cache",
			) as log_status:

				result, data, modified_index = (
					self.make_request (
						method = "GET",
						url = self.key_url (""),
						query_data = {
							"recursive": "true",
						},
						accept_response = [ 200 ]))

			self.cache_metadata = {
				"nodes": {},
			}

			self.update_cache (
				data ["node"],
				"")

			self.modified_index = (
				modified_index)

			self.write_cache_metadata ()

		self.watch_thread = (
			threading.Thread (
				target = self.watch_thread))

		self.watch_thread.daemon = True

		self.watch_thread.start ()

	def write_cache_metadata (self):

		self.cache_metadata ["modified-index"] = (
			unicode (self.modified_index))

		with open ("%s/metadata.temp" % self.cache_path, "w") \
		as file_handle:

			file_handle.write (
				yamlx.encode (
					None,
					self.cache_metadata))

		os.rename (
			"%s/metadata.temp" % self.cache_path,
			"%s/metadata" % self.cache_path)

	def watch_thread (self):

		self.connection.value = None
		self.connection.ssl_context = None
		self.connection.servers = list (self.servers)

		while True:

			result, data, modified_index = (
				self.make_request (
					method = "GET",
					url = self.key_url (""),
					query_data = {
						"recursive": "true",
						"wait": "true",
						"waitIndex": unicode (self.modified_index + 1),
					},
					accept_response = [ 200 ]))

			log.output (
				yamlx.encode (None, data))

			self.cache_metadata ["modified-index"] = (
				modified_index)

			self.update_cache (
				data ["node"],
				"")

	def update_cache (self, data, prefix):

		if data.get ("dir"):

			for node in data.get ("nodes", []):

				self.update_cache (
					node,
					data ["key"])

		else:

			self.cache_metadata ["nodes"] [data ["key"]] = (
				data ["modifiedIndex"])

			node_cache_path = (
				"%s/data%s" % (
					self.cache_path,
					data ["key"]))

			node_cache_dir_path = (
				os.path.dirname (
					node_cache_path))

			if not os.path.isdir (
				node_cache_dir_path):

				os.makedirs (
					node_cache_dir_path)

			with codecs.open (node_cache_path, "w", encoding = "utf-8") \
			as file_handle:

				file_handle.write (
					data ["value"])

	def get_connection (self):

		if os.getpid () == self.pid and self.connection.value:
			return self.connection.value

		if self.secure:

			if self.connection.ssl_context:

				connection = httplib.HTTPSConnection (
					host = self.connection.servers [0],
					port = self.port,
					key_file = self.client_key,
					cert_file = self.client_cert,
					context = self.connection.ssl_context,
					timeout = 4)

			else:

				connection = httplib.HTTPSConnection (
					host = self.connection.servers [0],
					port = self.port,
					key_file = self.client_key,
					cert_file = self.client_cert,
					timeout = 4)

			connection.connect ()

			if self.connection.ssl_context:

				peer_certificate = connection.sock.getpeercert ()
				peer_alt_names = peer_certificate ["subjectAltName"]

				# check if the server is an ip address

				if re.match (
					r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$",
					self.connection.servers [0]):

					# match ip addresses with custom code

					if not self.connection.servers [0] in [
						alt_value
						for alt_type, alt_value in peer_alt_names
						if alt_type == 'IP Address'
					]:

						raise Exception ("".join ([
							"Etcd server certificate failed to match IP address ",
							"'%s'" % self.connection.servers [0],
						]))

				else:

					# match hostnames using python implementation

					ssl.match_hostname (
						peer_certificate,
						self.connection.servers [0])

			self.connection.value = connection

		else:

			connection = httplib.HTTPConnection (
				host = self.connection.servers [0],
				port = self.port)

			connection.connect ()

			self.connection.value = connection

		self.pid = os.getpid ()

		return self.connection.value

	def key_url (self, key):

		return (
			"/v2/keys%s%s" % (
				self.prefix,
				key))

	def exists (self, key):

		result, data, modified_index = (
			self.make_request (
				method = "GET",
				url = self.key_url (key),
				accept_response = [ 200, 404 ]))

		if result == 200:
			return True

		if result == 404:
			return False

		raise Exception ()

	def get_raw_item (self, key):

		result, data, modified_index = (
			self.make_request (
				method = "GET",
				url = self.key_url (key),
				accept_response = [ 200, 404 ]))

		if result == 404:

			raise LookupError (
				"No such key: %s" % key)

		return EtcdRawItem (
			key,
			data ["node"])

	def get_raw (self, key):

		result, data, modified_index = self.make_request (
			method = "GET",
			url = self.key_url (key),
			accept_response = [ 200, 404 ])

		if result == 404:

			raise LookupError (
				"No such key: %s" % key)

		return data ["node"] ["value"]

	def get_raw_or_none (self, key):

		result, data, modified_index = (
			self.make_request (
				method = "GET",
				url = self.key_url (key),
				accept_response = [ 200, 404 ]))

		if result == 404:

			return None

		return data ["node"] ["value"]

	def set_raw_if_not_modified (self, key, value, index):

		result, data, modified_index = (
			self.make_request (
				method = "PUT",
				url = self.key_url (key),
				query_data = {
					"prevIndex": unicode (index),
				},
				payload_data = {
					"value": value,
				}))

	def set_raw (self, key, value):

		self.make_request (
			method = "PUT",
			url = self.key_url (key),
			payload_data = {
				"value": value,
			})

	def make_request (self, ** kwargs):

		for _ in itertools.repeat (5):

			try:

				return self.make_request_real (** kwargs)

			except (httplib.HTTPException, IOError):

				if self.connection.value:

					self.connection.value.close ()
					self.connection.value = None

				random.shuffle (self.connection.servers)

				time.sleep (1)

		return self.make_request_real (** kwargs)

	def make_request_real (
			self,
			method,
			url,
			query_data = {},
			payload_data = {},
			accept_response = [ 200, 201 ]):

		# prepare query

		query_string = (
			wbs.urlencode (
				query_data))

		if query_string:
			url += "&" if "?" in url else "?"
			url += query_string

		# prepare payload

		payload_bytes = (
			wbs.urlencode (
				payload_data))

		# get connection

		connection = self.get_connection ()

		# send request

		connection.putrequest (method, url)

		if payload_bytes:

			connection.putheader (
				"Content-Length",
				unicode (len (payload_bytes)))

			connection.putheader (
				"Content-Type",
				"application/x-www-form-urlencoded")

		connection.endheaders ()

		if payload_data:
			connection.send (payload_bytes)

		# read response

		response = connection.getresponse ()

		response_bytes = response.read ()

		# check response

		if not response.status in accept_response:

			raise Exception (
				"Error %s: %s" % (
					response.status,
					response.reason))

		# decode response

		if response.getheader ("Content-Type") == "application/json":

			return (
				response.status,
				json.loads (response_bytes.decode ("utf-8")),
				response.getheader ("X-Etcd-Index"),
			)

		else:

			return (
				response.status,
				None,
				None,
			)

	def update_raw (self, key, old_value, new_value):

		self.make_request (
			method = "PUT",
			url = self.key_url (key),
			payload_data = {
				"prevValue": old_value,
				"value": new_value,
			},
			accept_response = [ 200 ])

	def create_raw (self, key, value):

		status, data, modified_index = (
			self.make_request (
				method = "PUT",
				url = self.key_url (key),
				payload_data = {
					"value": value,
					"prevExist": "false",
				},
				accept_response = [ 201, 412 ]))

		if status == 412:

			raise ValueError (
				"Key already exists: %s" % key)

	def get_list (self, key):

		nodes = dict (self.get_tree (key))

		return [
			nodes ["/%s" % index]
			for index in xrange (0, len (nodes))
		]

	def get_tree (self, key):

		status, data, modified_index = (
			self.make_request (
				method = "GET",
				url = self.key_url (key),
				query_data = {
					"recursive": "true",
				},
				accept_response = [ 200, 201, 404 ]))

		if status == 404:
			return []

		return self.walk_tree (key, data ["node"])

	def walk_tree (self, prefix, node):

		if "value" in node:

			relative_key = node ["key"] [len (self.prefix) + len (prefix):]

			return [ (relative_key, node ["value"]) ]

		elif "nodes" in node:

			return [
				item for sub_list in [
					self.walk_tree (prefix, child_node)
					for child_node in node ["nodes"]
				] for item in sub_list
			]

		else:

			return []

	def rm (self, key):

		self.make_request (
			method = "DELETE",
			url = self.key_url (key),
			accept_response = [ 200 ])

	def rm_raw (self, key, value):

		self.make_request (
			method = "DELETE",
			url = self.key_url (key),
			query_data = {
				"prevValue": value,
			},
			accept_response = [ 200 ])

	def rm_recursive (self, key):

		self.make_request (
			method = "DELETE",
			url = self.key_url (key),
			query_data = {
				"recursive": "true",
			},
			accept_response = [ 200 ])

	def rmdir (self, key):

		self.make_request (
			method = "DELETE",
			url = self.key_url (key),
			query_data = {
				"dir": "true",
			},
			accept_response = [ 200 ])

	def mkdir_queue (self, key):

		status, data, modified_index = (
			self.make_request (
				method = "POST",
				url = self.key_url (key),
				query_data = {
					"dir": "true",
				},
				accept_response = [ 201 ]))

		return (
			data ["node"] ["key"] [len (self.prefix) : ],
			data ["node"] ["createdIndex"],
		)

	def get_yaml (self, key):

		raw_value = (
			self.get_raw_item (
				key))

		data_value = (
			yamlx.parse (
				raw_value.data))

		return EtcdYamlItem (
			self,
			raw_value,
			data_value)

	def set_yaml (self, key, value, schema = None):

		value_yaml = yamlx.encode (schema, value)

		self.set_raw (key, value_yaml)

	def set_yaml_if_not_modified (
			self,
			key,
			value,
			index,
			schema = None):

		value_yaml = (
			yamlx.encode (
				schema,
				value))

		self.set_raw_if_not_modified (
			key,
			value_yaml,
			index)

	def ls (self, key):

		status, data, modified_index = (
			self.make_request (
				method = "GET",
				url = self.key_url (key),
				accept_response = [ 200 ]))

		if not "nodes" in data ["node"]:
			raise Exception ()

		prefix_length = len (self.prefix) + len (key)

		return [
			node ["key"] [prefix_length + 1 : ]
			for node in data ["node"] ["nodes"]
		]

class EtcdRawItem (object):

	__slots__ = [
		"key",
		"data",
		"created_index",
		"modified_index",
	]

	def __init__ (self, key, node):

		self.key = key
		self.data = node ["value"]
		self.created_index = node ["createdIndex"]
		self.modified_index = node ["modifiedIndex"]

class EtcdYamlItem (collections.OrderedDict):

	__slots__ = [

		"client",
		"raw_item",
		"data",

		"created_index",
		"modified_index",
		"key",
		"raw_data",

	]

	def __init__ (self, client, raw_item, data):

		self.client = client
		self.raw_item = raw_item
		self.data = data

		self.created_index = raw_item.created_index
		self.modified_index = raw_item.modified_index
		self.key = raw_item.key
		self.raw_data = raw_item.data

		pass

	# ---------- update

	def save (self):

		self.client.set_yaml_if_not_modified (
			self.key,
			self.data,
			self.modified_index)

	# ---------- dictionary delegation

	def __contains__ (self, * arguments):

		return self.data.__contains__ (* arguments)

	def __delitem__ (self, * arguments):

		return self.data.__delitem__ (* arguments)

	def __getitem__ (self, * arguments):

		return self.data.__getitem__ (* arguments)

	def __iter__ (self, * arguments):

		return self.data.__iter__ (* arguments)

	def __len__ (self, * arguments):

		return self.data.__len__ (* arguments)

	def __length_hint__ (self, * arguments):

		return self.data.__length_hint__ (* arguments)

	def __reversed__ (self, * arguments):

		return self.data.__reversed__ (* arguments)

	def __setitem__ (self, * arguments):

		return self.data.__setitem__ (* arguments)

def args (sub_parsers):

	pass

# ex: noet ts=4 filetype=python
