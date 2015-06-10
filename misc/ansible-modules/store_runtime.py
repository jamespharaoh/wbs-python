#!/usr/bin/python

def main ():

	module = AnsibleModule (
		argument_spec = {},
		check_invalid_arguments = False,
		supports_check_mode = False)

	module.exit_json ()

main ()

# ex: noet ts=4 filetype=python
