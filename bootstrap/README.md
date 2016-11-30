Deploying DMon
==================

This document describes two alternative ways of deploying DMON:

* [Using Chef](#chef-bootstrap)
* [Using Cloudify](#cloudify-bootstrap)

Chef deployment
---------------

In a dedicated Ubuntu 14.04 host, first install the
[Chef Development Kit](https://downloads.chef.io/chef-dk/), e.g.:

```bash
$ wget https://packages.chef.io/stable/ubuntu/12.04/chefdk_0.19.6-1_amd64.deb
$ sudo dpkg -i chefdk_0.19.6-1_amd64.deb
```

Then obtain this cookbook repository:

```bash
$ git clone https://github.com/dice-project/DICE-Chef-Repository.git
$ cd DICE-Chef-Repository
```

Before we run the installation, we need to provide the configuration of the
DMon to be bootstrapped. We name the configuration file as `dmon.json` and
populate it with the following contents:

```json
{
  "dmon": {
    "openssl_conf": "[req]\ndistinguished_name = req_distinguished_name\nx509_extensions = v3_req\nprompt = no\n[req_distinguished_name]\nC = SL\nST = Slovenia\nL =  Ljubljana\nO = Xlab\nCN = *\n[v3_req]\nsubjectKeyIdentifier = hash\nauthorityKeyIdentifier = keyid,issuer\nbasicConstraints = CA:TRUE\nsubjectAltName = IP:172.16.117.200\n[v3_ca]\nkeyUsage = digitalSignature, keyEncipherment\nsubjectAltName = IP:172.16.117.200\n",
    "kb": {
      "ip": "0.0.0.0"
    }
  }
}
```

Replace *both* occurrences of the `172.16.117.200` IP from the
`"openssl_conf"` line with the IP of the node that you are installing the DMon
to.

Then use Chef client in its zero mode to execute the recipes:

```bash
$ sudo chef-client -z \
    -o recipe[dice_common::host],recipe[java::default],recipe[dmon::default],recipe[dmon::elasticsearch],recipe[dmon::kibana],recipe[dmon::logstash] \
    -j dmon.json
```


Cloudify deployment
-------------------

This process will create a new node in the target platform (FCO or OpenStack)
and install the whole DMon stack on top of it. It requires a Cloudify Manager
to be installed at the `CFY_MANAGER_HOST` address.

### Preparing environment

At the workstation node (i.e., our laptop, destkop PC where we install from),
we need to have the Cloudify Manager CLI installed. The following steps
are based on the [official documentation][CloudifyManagerBootstrap]:

For Redhat related GNU/Linux distributions, following packages need to be
installed: `python-virtualenv` and `python-devel`. Adjust properly for
Ubuntu and the like.

Now create new folder, create new python virtual environment and install
`cloudify` package.

    $ mkdir -p ~/dice && cd ~/dice
    $ virtualenv venv
    $ . venv/bin/activate
    $ pip install cloudify==3.4.0

Next we change to the directory containing the deployment blueprint and
connect the Cloudify CLI client to the Cloudify Manager. Note that
for the secured Cloudify Manager, we need to set the credentials in the
environment variables `CLOUDIFY_USERNAME` and `CLOUDIFY_PASSWORD`.

    $ cd ~/IeAT-DICE-Repository/bootstrap
    $ export CLOUDIFY_USERNAME=admin
    $ export CLOUDIFY_PASSWORD='OurCfyMngPassword'
    $ cfy -t $CFY_MANAGER_HOST

[CloudifyManagerBootstrap]:http://docs.getcloudify.org/3.4.0/manager/bootstrapping/

### Preparing inputs

The blueprint deployment needs a few parameters to be specified at this point.
Use an `inputs-$PLATFORM.example.yaml` for your platform as a template to fill
in, e.g., for the OpenStack:

    $ cp inputs-openstack.example.yaml inputs-openstack.yaml

Use a text editor to replace the values set in the inputs template with the
values that will apply to your deploy. To do this, follow the comments in the
`inputs-openstack.yaml` file.

### Executing deployment

To run the deployment of the DMon blueprint, use convenience scripts (which, in
turn, call `cfy`):

    $ ./up.sh openstack dmon-main

Here, `openstack` is the target platform, and the script will use this name to
choose the blueprint file (`openstack.yaml`) and the inputs file
(`inputs-openstack.yaml`). The `dmon-main` string names the deployment in the
Cloudify Manager.

### Removing deployment

The DMon deployment can be uninstalled using the following call:

    $ ./dw.sh dmon-main
