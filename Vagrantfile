require "rbconfig"

include RbConfig

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure VAGRANTFILE_API_VERSION do
	|config|

	# general config

	config.vm.box = "ubuntu/trusty64"

	config.vm.hostname = "wistla-dev"

	config.vm.network "private_network",
		ip: "172.28.128.3"

	config.ssh.forward_agent = true

	# network routing

	case CONFIG["host_os"]

	when "linux-gnu"

		config.trigger.after :up do
			run "sudo route add -net 10.210.0.0 netmask 255.255.0.0 gw 172.28.128.3"
		end

		config.trigger.after :down do
			run "sudo route del -net 10.210.0.0 netmask 255.255.0.0 gw 172.28.128.3"
		end

	when "darwin"

		config.trigger.after :up do
			run "sudo route add -net 10.210.0.0/16 172.28.128.3"
		end

		config.trigger.after :down do
			run "sudo route del -net 10.210.0.0/16 172.28.128.3"
		end

	end

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
