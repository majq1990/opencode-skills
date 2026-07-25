## oneinstall for egova

- Requires Ansible 1.2 or newer
- Expects CentOS/RHEL 7.x hosts

These playbooks deploy a very basic implementation of micro-service
. To use them, first edit the `inventory.ini` inventory file to contain the
hostnames of the machines on which you want service or database deployed, and edit the 
group_vars/all.yml file to set any micro-service configuration parameters you need.

Then run the playbook, like this:

	ansible-playbook -i hosts site.yml

- common
    patch for mini centos
- redis

- minio

- nginx

- mysql

- microservice