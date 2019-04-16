#
# Copyright (c) 2019 StarlingX.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

# All Rights Reserved.
#

""" Define NovaProvider class
This class wraps novaclient access interface and expose get_instance() and
get_instances() to other agent classes.
"""

import keyring
from novaclient import client
from keystoneauth1 import loading
from keystoneauth1 import session
import socket
from Log import LOG
from config import CONF
from config import sysconfig
import instance
import guest


class NovaProvider:

    def __init__(self):
        self._creds = self._get_keystone_creds()
        self._auth = self._get_auth(self._creds)
        self._hostname = self.get_hostname()

    def get_hostname(self):
        return socket.gethostname()

    def _get_keystone_creds(self):
        creds = {}
        keyStoneSession = 'openstack_keystone_authtoken'
        options = ['username', 'user_domain_name', 'project_name',
                   'project_domain_name', 'keyring_service']

        try:
            for option in options:
                creds[option] = sysconfig.get(keyStoneSession, option)

            creds['password'] = keyring.get_password(creds.pop('keyring_service'),
                                                     creds['username'])
            creds['auth_url'] = CONF.auth_url
        except Exception as e:
            LOG.error("Could not get keystone creds configuration! Err=%s" % e)
            creds = None

        return creds

    def _get_auth(self, creds):

        if creds is not None:
            loader = loading.get_plugin_loader('password')
            auth = loader.load_from_options(**creds)
            return auth
        return None

    def get_nova(self):
        try:
            sess = session.Session(auth=self._auth)
            nova = client.Client('2.1', session=sess)
            return nova
        except Exception as e:
            LOG.warning("Failed to connect to nova!")
            raise Exception("could not connect nova!")

    def get_instance(self, uuid):
        try:
            nova = self.get_nova()
            server = nova.servers.get(uuid)
            flavor_info = nova.flavors.get(server.flavor["id"])
            hostname = server.__dict__['OS-EXT-SRV-ATTR:host']
        except Exception as e:
            LOG.warning("Could not get instance=%s from Nova! error=%s" % (uuid, e))
            return None

        LOG.debug('GET VM:%s in node:%s' % (server.name, hostname))

        if hostname == self._hostname:
            inst = instance.instance(uuid, server.name, flavor_info.extra_specs)
            # get numa topology and pci info from libvirt
            conn = guest.connect_to_libvirt()
            domain = guest.get_guest_domain_by_uuid(conn, self.uuid)
            conn.close()
            inst.update(domain)
            return inst
        else:
            LOG.debug('The VM is not in current host!')
            return None

    def get_instances(self, filters):
        instances = set()
        try:
            nova = self.get_nova()
            filters['host'] = self._hostname
            servers = nova.servers.list(detailed=True, search_opts=filters)
            flavors = nova.flavors.list()

            for server in servers:
                for flavor in flavors:
                    if flavor.id == server.flavor["id"]:
                        if 'hw:cpu_policy' in flavor.extra_specs \
                                and flavor.extra_specs['hw:cpu_policy'] == 'dedicated':
                            inst = instance.instance(server.id, server.name, flavor.extra_specs)
                            instances.update([inst])
            # get numa topology and pci info from libvirt
            if len(instances) > 0:
                conn = guest.connect_to_libvirt()
                for inst in instances:
                    domain = guest.get_guest_domain_by_uuid(conn, inst.uuid)
                    inst.update(domain)
                conn.close()

        except Exception as e:
            LOG.warning("Failed to get instances from Nova! error=%s" % e)

        return instances


novaClient = NovaProvider()
