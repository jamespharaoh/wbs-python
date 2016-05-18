#!/usr/bin/env python

import site

site.addsitedir ("work/lib/python2.7/site-packages")

import git

git_repo = (
	git.Repo ("."))

git_origin = (
	git_repo.remotes.origin)

new_merged = (
	git_repo.refs ["master"].commit)

old_master = (
	git_repo.refs ["origin/master"].commit)

if new_merged == old_master:

	if "origin/automerge" in git_repo.refs:

		print (
			"Removing branch: automerge")

		git_origin.push (
			":automerge")

	else:

		print (
			"Nothing to do")

	# TODO remove pull request?

else:

	if "origin/automerge" in git_repo.refs:

		print (
			"Updating branch: automerge")

		git_origin.push (
			"master:automerge",
			force = True)

	else:

		print (
			"Creating branch: automerge")

		git_origin.push (
			"master:automerge")

	# TODO create pull request

# ex: et ts=4 filetype=python
