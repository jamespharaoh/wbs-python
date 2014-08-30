VAGRANTFILE_API_VERSION = "2"

Vagrant.configure VAGRANTFILE_API_VERSION do
	|config|

	config.vm.box = "hashicorp/precise64"

	config.ssh.forward_agent = true

	# run provisioning scripts

	config.vm.provision "shell",
		path: "etc/provision-root",
		privileged: true

	config.vm.provision "shell",
		path: "etc/provision-user",
		privileged: false

end

# ex: noet ts=4 filetype=ruby
