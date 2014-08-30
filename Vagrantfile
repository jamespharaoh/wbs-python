VAGRANTFILE_API_VERSION = "2"

Vagrant.configure VAGRANTFILE_API_VERSION do
	|config|

	# general config

	config.vm.box = "ubuntu/trusty64"

	config.ssh.forward_agent = true

	# setup ansible

	config.vm.provision "shell",
		path: "etc/ansible-setup",
		privileged: true

	# run ansible

	config.vm.provision "shell",
		path: "etc/ansible-invoke",
		privileged: true

end

# ex: noet ts=4 filetype=ruby
