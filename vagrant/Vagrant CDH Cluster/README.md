# Cloudera Vagrant Installation

__NOTE: Because of the computationally heavy nature of CDH 5.4.0 the virtual cluster consumes approximately 10 GB of RAM. You would need at least 16 GB of RAM on the host in order to effectively use this cluster.*__


First VirtualBox or VMWare Player/Fusion has to be installed:
* [VirtualBox Windows Installation](http://download.virtualbox.org/virtualbox/4.3.28/VirtualBox-4.3.28-100309-Win.exe)
* [VirtualBox Linux Installation](https://www.virtualbox.org/wiki/Linux_Downloads)

The Vagrant has to be installed:
* [Windows Vagrant Installation](https://dl.bintray.com/mitchellh/vagrant/vagrant_1.7.2.msi) 
* [Linux vagrant Installation](https://dl.bintray.com/mitchellh/vagrant/vagrant_1.7.2.msi)

Install Vagrant host manager plugin (terminal or cmd):
```
 vagrant plugin install vagrant-hostmanager
```

__NOTE: I would also recommend installing vagrant snapshot tool__

```
 vagrant plugin install vagrant-vbox-snapshot
```

Once this is done download the vagrant configuration file into the directory in which you want the virtual cluster to be set up.
* You can clone the up to date file from https://github.com/igabriel85/DICE-Project.git
** The first part of this file contains an initialization script for CDH 5.4.0 which can be used outside of this configuration

This will create 4 VMs, one master and 3 slaves. Each running Ubuntu 12.04 64bit. It will install at startup the following important packages:
* Oracle Java JDK 1.7 
* Cloudera-manager-server
* Cloudera-manager-demon
* Cloudera-manager-server-db


Currently the master VM's RAM is set to 4096 MB and the slave memory is set to 2048 RAM. You can edit these values at: _v.customize ["modifyvm", :id, "--memory", "4096"]_.

It is important to mention that the IPs and hostnames are set automatically using the vagrant host manager plugin:
* master: 10.211.55.100 
* slave1: 10.211.55.101 
* slave2: 10.211.55.102 
* slave3: 10.211.55.103

In the directory containing the Vagrantfile run the command:

```
 vagrant up
```

The startup usually takes some time, depending on the host machine.
To access the running machines use:
* vagrant ssh _<hostname>_  
* user: vagrant password: vagrant
* On windows putty is required
 * master ssh port 2200
 * slave1 ssh port 2222
 * slave2 ssh port 2201
 * slave3 ssh port 2202

Once the VMs are up and cloudera manager has started it will be posible to access the Cloudera manager WUI at: 
* [http://vm-cluster-oryx1:7180](http://vm-cluster-oryx1:7180)

In order to stop the virtual cluster run:

```
 vagrant suspend
```
Reactivate the virtual cluster
```
 vagrant resume
```
