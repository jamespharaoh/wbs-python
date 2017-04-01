from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gridlinker.module import module_build

__all__ = [
	"args",
]

def args (prev_sub_parsers):

	parser = prev_sub_parsers.add_parser (
		"module",
		help = "manage gridlinker modules")

	next_sub_parsers = parser.add_subparsers ()

	args_module_build (next_sub_parsers)

def args_module_build (sub_parsers):

	parser = sub_parsers.add_parser (
		"build",
		help = "build modules")

	parser.set_defaults (
		func = do_module_build)

def do_module_build (context, args):

	module_build.build_modules (
		context = context,
		module_names = None)

# ex: noet ts=4 filetype=python
