from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import flask
import flask.ext.assets
import os
import wbs
import werkzeug
import yaml

from wbs import *

class WbsDocsServer ():

	def __init__ (self, master, content):

		self.master = master
		self.content = content

		self.load_settings ()

		self.init_project ()
		self.init_login ()

		self.init_flask ()
		self.init_styles ()
		self.init_routes ()

	def load_settings (self):

		self.settings = (
			yamlx.load_data (
				"config/settings"))

	def init_project (self):

		self.project = wbs.Project (
			title = "WBS Documentation")

	def init_login (self):

		self.login_client = (
			wbs.LoginClient (
				self.settings ["security"]))

	def init_flask (self):

		self.flask = (
			flask.Flask (
				"wbs-documentation"))

		self.flask.config ["DEBUG"] = (
			self.settings ["server"] ["debug"] == "yes")

		self.flask.config ["SERVER_NAME"] = (
			self.settings ["server"] ["hostname"])

		self.flask.before_request (
			self.before_request)

	def init_styles (self):

		self.assets = (
			flask.ext.assets.Environment (
				self.flask))

		self.assets.url = (
			self.flask.static_url_path)

		self.scss = flask.ext.assets.Bundle (
			"styles/wbs/main.scss",
			"styles/wbs/fonts.scss",
			"styles/wbs/header.scss",
			"styles/wbs/navigation.scss",
			"styles/wbs/content.scss",
			"styles/wbs/syntax.scss",
			filters = "pyscss",
			output = "styles/all.css")

		self.assets.register (
			"scss_all",
			self.scss)

	def init_routes (self):

		self.flask.register_error_handler (
			403,
			self.error_forbidden)

		self.flask.register_error_handler (
			404,
			self.error_not_found)

		self.flask.add_url_rule (
			rule = "/",
			endpoint = "root",
			view_func = self.route_content,
			defaults = dict (
				path = ""))

		self.flask.add_url_rule (
			rule = "/<path:path>",
			endpoint = "content",
			view_func = self.route_content)

	def run (self):

		extra_dirs = [
			"content",
		]

		extra_files = extra_dirs [:]

		for extra_dir in extra_dirs:
			for dirname, dirs, files in os.walk (extra_dir):
				for filename in files:
					filename = os.path.join (dirname, filename)
					if os.path.isfile (filename):
						extra_files.append (filename)

		self.flask.run (
			host = self.settings ["server"] ["listen-address"],
			port = int (self.settings ["server"] ["listen-port"]))

	def before_request (self):

		flask.g.project = self.project

		self.login_client.before_request ()

	def error_forbidden (self, exception):

		return (
			flask.render_template (
				"error-forbidden.html",
				title = "Access denied",
				entry = self.content.find_entry ("")),
			403)

	def error_not_found (self, exception):

		return (
			flask.render_template (
				"error-not-found.html",
				title = "Not found",
				entry = self.content.find_entry ("")),
			404)

	def route_root (self, name):

		self.route_content ("")

	def route_styles (self, name):

		styles_path = "/".join ([
			self.master.home,
			"styles",
			name,
		])

		with open (styles_path) as file_handle:
			styles_source = file_handle.read ()

		styles_data = list (yaml.load (styles_source))

		styles_css = ""

		for style_data in styles_data:

			styles_css += (
				"%s {\n" % (
					style_data ["match"]))

			for rule_name, rule_data in style_data ["rules"].items ():

				styles_css += (
					"\t%s: %s;\n" % (
						rule_name,
						rule_data))

			styles_css += (
				"}\n");

		return (
			styles_css,
			"200",
			dict ({
				"content-type": "text/css",
			}),
		)

	def route_content (self, path):

		entry = self.content.find_entry (path)

		if not entry:

			raise werkzeug.exceptions.NotFound ()

		if not entry.can_view (flask.g.user_groups):

			raise werkzeug.exceptions.Forbidden ()

		page_html = flask.render_template (
			"entry.html",
			content = self.content,
			title = entry.long_title,
			entry = entry)

		return page_html

# ex: noet ts=4 filetype=python
