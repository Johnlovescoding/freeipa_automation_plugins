# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


#### Imports ##################################################################
import functools
import logging
from ipalib import _, ngettext
from ipalib import api, errors, output, Command
from ipalib.output import Output, Entry, ListOfEntries
from .baseldap import (
    LDAPObject,
    LDAPCreate,
    LDAPUpdate,
    LDAPSearch,
    LDAPDelete,
    LDAPRetrieve)
from ipalib.parameters import *
from ipalib.plugable import Registry
from ipapython.dn import DN
from ipapython.dnsutil import DNSName
from netaddr import *
#from trietree import *
import re
import time
from poolds import *
import fcntl
import os
#import string

# logging.basicConfig(level=logging.WARNING,
#                     filename='/var/log/ipa-alm/debug_log',
#                     filemode='w',
#                     format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'
#                     )

#step 1, create a logger
# logger = logging.getLogger(__name__) #生成logger instance，命名为alm
# logger.setLevel(logging.INFO) # Log等级总开关
#
# #step 2, create a handler to write logfile
# logfile = '/var/log/ipa-alm/debug_log'
# fh = logging.FileHandler(logfile, mode = 'w')
# fh.setLevel((logging.DEBUG))
#
# #step 3, define the format
# formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
# fh.setFormatter(formatter)
#
# #step 4, add handler into logger
# logger.addHandler(fh)

#logger = logging.getLogger(__name__)

# formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
# file_handler = logging.FileHandler("test.log")
#### lock file mechanisam for multi-write from different users at same time#################

global_lock_file_path = '/var/lock/ipa-alm/'

def _try_lock(self_lock_file_path):
    """Check and create lock file
    Return lock file handler.
    """
    lock_file = open(self_lock_file_path, "w")  # create a lock_file
    try:
        fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_file
    except:
        return None

def _unlock(fhandler):
    """Unlock app - remove lock file ``fhandler``."""
    fname = fhandler.name
    try:
        #time.sleep(3)
        fhandler.close()
        os.unlink(fname)
    except IOError as err:
        raise BaseException("unlock error: %s", err)

def _add_lock(objectname, cn):
    cn = cn.replace('/', '-')
    lock_file_path = global_lock_file_path + 'write' + '-' + objectname + '-' + cn
    fhandler = _try_lock(lock_file_path)
    if fhandler is None:
        count = 30
        while (count > 0 and fhandler is None): #try 30 times to lock the file in half minute
            time.sleep(1)
            count -= 1
            fhandler = _try_lock(lock_file_path)
    return fhandler

def lockdecorator(func):
    @functools.wraps(func)
    def wrapper(self, *keys, **options):
        segments = self.__class__.__name__.split("_") #ex: almleases_mod_almschema
        fileheader = ""
        if len(segments) > 0 :
            fileheader = segments[0]
        else :
            raise errors.PublicError('Cannot find Class Name of this Method')
        # / / / / / / / / / add a lock file here / / / / / / / / / / *
        if len(keys) > 0:
            cn = keys[0]
        else :
            cn = 'NotFound'
            raise errors.PublicError('Cannot find cn of this entry')

        fhandler = _add_lock(fileheader, cn) #object_name
        logging.warning(fileheader)
        logging.warning(cn)
        try:
            if fhandler:
                return func(self, *keys, **options)
        finally:
            if fhandler:
                #time.sleep(20)
                _unlock(fhandler)
            else:
                return dict(result=dict(result=False, value=u'other user is locking this entry'), value=cn)
    return wrapper
#### Constants ################################################################


containerdn = DN(('cn', 'alm'))
pool_container_dn = DN(('cn', 'pool'), containerdn) #每个LDAPOject中的container_dn为存该entry的container目录，不需要定义完全，LDAP会自动存到api.env.basedn中
lease_container_dn = DN((('cn', 'lease')), containerdn)#在update文件中，先定义alm, pool, lease三个almservice  entry作为container用


register = Registry()


#### almservice ##############################################################


@register()
class almservice(LDAPObject):
    container_dn = containerdn
    object_name = _('alm configuration')
    object_name_plural = _('alm configuration')
    object_class = ['almservice']
    label = _('alm Configuration')
    label_singular = _('alm Configuration')

    managed_permissions = {
        'System: Read alm Configuration': {
            'non_object': True,
            'ipapermlocation': api.env.basedn,
            'ipapermtarget': DN('cn=alm', api.env.basedn),
            'replaces_global_anonymous_aci': True,
            'ipapermbindruletype': 'anonymous',
            'ipapermright': {'read', 'search', 'compare'},
            'ipapermdefaultattr':           {
                'cn', 'objectclass',
                'almprimarydn', 'almsecondarydn',
                'almnetmask',
                'almrange', 'almpermitlist',
                'almservicedn',
                'almHWAddress',
                'almstatements', 'almoption', 'almcomments'
            },
        },
        'System: Write alm Configuration': {
            'non_object': True,
            'ipapermright': {'write'},
            'ipapermlocation': api.env.basedn,
            'ipapermtarget': DN('cn=alm', api.env.basedn),
            'ipapermtargetfilter': ['(objectclass=almservice)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'almprimarydn', 'almsecondarydn',
                'almstatements', 'almoption', 'almcomments'
            },
            'default_privileges': {'alm Administrators'},
        },
    }

    takes_params = (
        DNParam(
            'almprimarydn?',
            cli_name='primarydn',
            label=_('Primary Server'),
            doc=_('Primary server DN.')
        ),
        DNParam(
            'almsecondarydn*',
            cli_name='secondarydn',
            label=_('Secondary Servers'),
            doc=_('Secondary server DN.')
        ),
        Str(
            'almstatements*',
            cli_name='almstatements',
            label=_('alm Statements'),
            doc=_('alm statements.')
        ),
        Str(
            'almoption*',
            cli_name='almoptions',
            label=_('alm Options'),
            doc=_('alm options.')
        ),
        Str(
            'almcomments?',
            cli_name='almcomments',
            label=_('Comments'),
            doc=_('alm comments.')
        ),
        Int(
            'defaultleasetime?',
            cli_name='defaultleasetime',
            label=_('Default Lease Time'),
            doc=_('Default lease time.'),
            flags=['virtual_attribute']
        ),
        Int(
            'maxleasetime?',
            cli_name='maxleasetime',
            label=_('Maximum Lease Time'),
            doc=_('Maximum lease time.'),
            flags=['virtual_attribute']
        ),

    )

    def get_almservice(self, ldap):
        entry = ldap.get_entry(self.get_dn(), None)
        return entry

    def get_dn(self, *keys, **kwargs):
        if not almservice.almservice_exists(self.api.Backend.ldap2):
            raise errors.NotFound(reason=_('alm is not configured'))
        return DN(self.container_dn, api.env.basedn)

    @staticmethod
    def almservice_exists(ldap):
        container_dn = DN(('cn', 'alm'))
        try:
            ldap.get_entry(DN(container_dn, api.env.basedn), [])
        except errors.NotFound:
            return False
        return True

    @staticmethod
    def extract_virtual_params(ldap, dn, entry_attrs, keys, options):
        almStatements = entry_attrs.get('almstatements', [])

        for statement in almStatements:
            if statement.startswith('default-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['defaultleasetime'] = v
            if statement.startswith('max-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['maxleasetime'] = v

        almOptions = entry_attrs.get('almoption', [])

        for option in almOptions:
            if option.startswith('domain-name '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainname'] = v.replace('"', '')
            if option.startswith('domain-name-servers '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainnameservers'] = v.split(', ')
            if option.startswith('domain-search '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainsearch'] = v.replace('"', '').split(', ')

        return entry_attrs


@register()
class almservice_show(LDAPRetrieve):
    __doc__ = _('Display the alm configuration.')

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = almservice.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class almservice_mod(LDAPUpdate):
    __doc__ = _('Modify the alm configuration.')
    msg_summary = _('Modified the alm configuration.')

    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)

        if 'almstatements' in entry_attrs:
            almStatements = entry_attrs.get('almstatements', [])
        else:
            entry = ldap.get_entry(dn)
            almStatements = entry.get('almstatements', [])

        if 'defaultleasetime' in options:
            statement = 'default-lease-time {0}'.format(options['defaultleasetime'])
            foundStatement = False
            for i, s in enumerate(almStatements):
                if s.startswith('default-lease-time '):
                    foundStatement = True
                    almStatements[i] = statement
                    break
            if not foundStatement:
                almStatements.append(statement)

        if 'maxleasetime' in options:
            statement = 'max-lease-time {0}'.format(options['maxleasetime'])
            foundStatement = False
            for i, s in enumerate(almStatements):
                if s.startswith('max-lease-time '):
                    foundStatement = True
                    almStatements[i] = statement
                    break
            if not foundStatement:
                almStatements.append(statement)

        if 'almoption' in entry_attrs:
            almOptions = entry_attrs.get('almoption', [])
        else:
            entry = ldap.get_entry(dn)
            almOptions = entry.get('almoption', [])

        entry_attrs['almstatements'] = almStatements
        entry_attrs['almoption'] = almOptions

        return dn

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = almservice.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


#### almpool ###############################################################

@register()
class almpool(LDAPObject):

    #parent_object = 'almservice'
    container_dn = pool_container_dn
    object_name = _('alm pool')
    object_name_plural = _('alm pools')
    object_class = ['almpool']
    label = _('alm Pools')
    label_singular = _('alm Pool')

    search_attributes = ['cn', 'almrange']

    managed_permissions = {
        'System: Add alm Pools': {
            'ipapermright': {'add'},
            'ipapermtargetfilter': ['(objectclass=almpool)'],
            'default_privileges': {'alm Administrators'},
        },
        'System: Modify alm Pools': {
            'ipapermright': {'write'},
            'ipapermtargetfilter': ['(objectclass=almpool)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass', 'almpooltype',
                'almrange', 'almpermitlist',
                'almprimarydn', 'almsecondarydn',
                'almstatements', 'almoption', 'almcomments'
            },
            'default_privileges': {'alm Administrators'},
        },
        'System: Remove alm Pools': {
            'ipapermright': {'delete'},
            'ipapermtargetfilter': ['(objectclass=almpool)'],
            'default_privileges': {'alm Administrators'},
        }
    }

    takes_params = (
        Str(
            'cn',
            cli_name='poolname',
            label=_('Pool Name'),
            doc=_('alm pool name.'),
            primary_key=True
        ),
        Str(
            'almpooltype',
            cli_name='type',
            label=_('Type'),
            doc=_('alm pool type')
        ),
        Str(
            'almrange',
            cli_name='range',
            label=_('Range'),
            doc=_('alm range.')
        ),
        Str(
            'almpermitlist*',
            cli_name='permitlist',
            label=_('Permit List'),
            doc=_('alm permit list.')
        ),
        Str(
            'almstatements*',
            cli_name='almstatements',
            label=_('alm Statements'),
            doc=_('alm statements.')
        ),
        Str(
            'almoption*',
            cli_name='almoptions',
            label=_('alm Options'),
            doc=_('alm options.')
        ),
        Str(
            'almcomments?',
            cli_name='almcomments',
            label=_('Comments'),
            doc=_('alm comments.')
        ),
        Int(
            'defaultleasetime?',
            cli_name='defaultleasetime',
            label=_('Default Lease Time'),
            doc=_('Default lease time.'),
            flags=['virtual_attribute']
        ),
        Int(
            'maxleasetime?',
            cli_name='maxleasetime',
            label=_('Maximum Lease Time'),
            doc=_('Maximum lease time.'),
            flags=['virtual_attribute']
        ),
        Bool(
            'permitknownclients?',
            cli_name='permitknownclients',
            label=_('Permit Known Clients'),
            doc=_('Permit known clients.'),
            flags=['virtual_attribute']
        ),
        Bool(
            'permitunknownclients?',
            cli_name='permitunknownclients',
            label=_('Permit Unknown Clients'),
            doc=_('Permit unknown clients.'),
            flags=['virtual_attribute']
        ),
    )

    @staticmethod
    def extract_virtual_params(ldap, dn, entry_attrs, keys, options):

        almPermitList = entry_attrs.get('almpermitlist', [])

        for item in almPermitList:
            if item.endswith(' known-clients'):
                if item.startswith('allow '):
                    entry_attrs['permitknownclients'] = True
                elif item.startswith('deny '):
                    entry_attrs['permitknownclients'] = False
            if item.endswith(' unknown-clients'):
                if item.startswith('allow '):
                    entry_attrs['permitunknownclients'] = True
                elif item.startswith('deny '):
                    entry_attrs['permitunknownclients'] = False

        almStatements = entry_attrs.get('almstatements', [])

        for statement in almStatements:
            if statement.startswith('default-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['defaultleasetime'] = v
            if statement.startswith('max-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['maxleasetime'] = v

        almOptions = entry_attrs.get('almoption', [])

        for option in almOptions:
            if option.startswith('domain-name '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainname'] = v.replace('"', '')
            if option.startswith('domain-name-servers '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainnameservers'] = v.split(', ')
            if option.startswith('domain-search '):
                (o, v) = option.split(' ', 1)
                entry_attrs['domainsearch'] = v.replace('"', '').split(', ')

        return entry_attrs


@register()
class almpool_add_almschema(LDAPCreate):
    __doc__ = _('Create a new alm pool.')
    msg_summary = _('Created alm pool "%(value)s"')

    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)
        #container_dn = DN('cn=pool', 'cn=alm')
        # Allow known and unknown clients by default.



        entry_attrs['almpermitlist'] = ['allow unknown-clients', 'allow known-clients']

        # If the almService entry has almstatements attributes that start with
        # "default-lease-time" or "max-lease-time", grab them and copy their
        # values into the new pool. This code could probably be a lot more
        # efficient, but it works. The blame REALLY lies with the author of the
        # alm LDAP schema for being so lazy.

        hasDefaultLeaseTime = False
        hasMaxLeaseTime = False

        if 'almstatements' in entry_attrs:
            for statement in entry_attrs['almstatements']:
                if statement.startswith('default-lease-time'):
                    hasDefaultLeaseTime = True
                if statement.startswith('max-lease-time'):
                    hasMaxLeaseTime = True

        if hasDefaultLeaseTime and hasMaxLeaseTime:
            return dn

        config = ldap.get_entry(DN(pool_container_dn, api.env.basedn))

        if 'almStatements' in config:
            configalmStatements = config['almStatements']
        else:
            configalmStatements = []

        defaultLeaseTime = None
        maxLeaseTime = None

        for statement in configalmStatements:
            if statement.startswith('default-lease-time'):
                (s, v) = statement.split(" ")
                defaultLeaseTime = v
            if statement.startswith('max-lease-time'):
                (s, v) = statement.split(" ")
                maxLeaseTime = v

        if 'almstatements' in entry_attrs:
            entryalmStatements = entry_attrs['almstatements']
        else:
            entryalmStatements = []

        if defaultLeaseTime is not None:
            foundStatement = False
            for i, s in enumerate(entryalmStatements):
                if s.startswith('default-lease-time'):
                    foundStatement = True
                    entryalmStatements[i] = 'default-lease-time {0}'.format(defaultLeaseTime)
                    break
            if foundStatement is False:
                entryalmStatements.append('default-lease-time {0}'.format(defaultLeaseTime))

        if maxLeaseTime is not None:
            foundStatement = False
            for i, s in enumerate(entryalmStatements):
                if s.startswith('max-lease-time'):
                    foundStatement = True
                    entryalmStatements[i] = 'max-lease-time {0}'.format(maxLeaseTime)
                    break
            if foundStatement is False:
                entryalmStatements.append('max-lease-time {0}'.format(maxLeaseTime))

        entry_attrs['almstatements'] = entryalmStatements

        return dn


@register()
class almpool_find(LDAPSearch):
    __doc__ = _('Search for a alm pool.')
    msg_summary = ngettext(
        '%(count)d alm pool matched',
        '%(count)d alm pools matched', 0
    )


@register()
class almpool_show(LDAPRetrieve):
    __doc__ = _('Display a alm pool.')

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = almpool.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class almpool_mod_almschema(LDAPUpdate):
    __doc__ = _('Modify a alm pool.')
    msg_summary = _('Modified a alm pool.')

    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):

        assert isinstance(dn, DN)

        entry = ldap.get_entry(dn)

        if 'almpermitlist' in entry_attrs:
            almPermitList = entry_attrs.get('almpermitlist', [])
        else:
            almPermitList = entry.get('almpermitlist', [])

        if 'permitknownclients' in options:
            item = '{0} known-clients'.format('allow' if options['permitknownclients'] else 'deny')
            newPermitList = [p for p in almPermitList if not p.endswith(' known-clients')]
            newPermitList.append(item)
            almPermitList = newPermitList

        if 'permitunknownclients' in options:
            item = '{0} unknown-clients'.format('allow' if options['permitunknownclients'] else 'deny')
            newPermitList = [p for p in almPermitList if not p.endswith(' unknown-clients')]
            newPermitList.append(item)
            almPermitList = newPermitList

        entry_attrs['almpermitlist'] = almPermitList

        if 'almstatements' in entry_attrs:
            almStatements = entry_attrs.get('almstatements', [])
        else:
            almStatements = entry.get('almstatements', [])

        if 'defaultleasetime' in options:
            statement = 'default-lease-time {0}'.format(options['defaultleasetime'])
            foundStatement = False
            for i, s in enumerate(almStatements):
                if s.startswith('default-lease-time '):
                    foundStatement = True
                    almStatements[i] = statement
                    break
            if not foundStatement:
                almStatements.append(statement)

        if 'maxleasetime' in options:
            statement = 'max-lease-time {0}'.format(options['maxleasetime'])
            foundStatement = False
            for i, s in enumerate(almStatements):
                if s.startswith('max-lease-time '):
                    foundStatement = True
                    almStatements[i] = statement
                    break
            if not foundStatement:
                almStatements.append(statement)

        entry_attrs['almstatements'] = almStatements

        if 'almoption' in entry_attrs:
            almOptions = entry_attrs.get('almoption', [])
        else:
            almOptions = entry.get('almoption', [])

        entry_attrs['almoption'] = almOptions

        return dn



    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = almpool.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn

    @lockdecorator
    def execute(self, *keys, **options):
        result = super(self.__class__, self).execute(*keys, **options)
        return result

@register()
class almpool_mod_nolock(LDAPUpdate):
    __doc__ = _('Modify a alm pool without lock.')
    msg_summary = _('Modified a alm pool without lock.')


@register()
class almpool_del_almschema(LDAPDelete):
    __doc__ = _('Delete a alm pool.')
    msg_summary = _('Deleted alm pool "%(value)s"')


@register()
class almpool_is_valid(Command):
    NO_CLI = True
    has_output = output.standard_boolean
    msg_summary = _('"%(value)s"')

    takes_args = (  ##takes_args必须要两个参数？
        Str(
            'almsubnetcn',
            cli_name='subnet',
            label=_('Subnet'),
            doc=_('alm subnet.')
        ),
        Str(
            'almrange+',
            cli_name='range',
            label=_('Range'),
            doc=_('alm range.')
        )
    )

    def execute(self, *args, **kw): #函数的参数定义是(*args, **kw)，因此，execute()函数可以接受任意参数的调用
        # Run some basic sanity checks on a alm pool IP range to make sure it
        # fits into its parent alm subnet. This method looks up the parent
        # subnet given the necessary LDAP keys because that's what works best
        # with the GUI.

        ##        almsubnetcn = args[0]
        almrange = args[1][0]

        (rangeStart, rangeEnd) = almrange.split(" ")
        rangeStartIP = IPNetwork("{0}/32".format(rangeStart))
        rangeEndIP = IPNetwork("{0}/32".format(rangeEnd))

        if rangeStartIP > rangeEndIP:
            return dict(result=False, value=u'First IP must come before last IP!')
        return dict(result=True, value=u'Valid IP range.')


############################################add pattern error to mod_pool
@register()
class almpool_add(Command):
    has_output = output.standard_entry
    __doc__ = _('Create a new alm pool.')
    msg_summary = _('Created alm pool "%(value)s"')

    takes_args = (
        Str(
            'cn',
            cli_name='poolname',
            label=_('Poolname'),
            doc=_("Poolname.")
        ),
        Str(
            'almpooltype',
            cli_name='type',
            label=_('Type'),
            doc=_('alm pool type')
        ),
        Str(
            'almrange',
            cli_name='range',
            label=_('Range'),
            doc=_('alm range.')
        )
    )

    def execute(self, *args, **kw):
        cn = args[0]
        pooltype = args[1]
        poolrange = args[2]

        typelist = ['ipv4', 'ipv6', 'macaddress', 'string']

        if pooltype.lower().replace(' ', '') not in typelist:
            return dict(result = dict(result=False, value=u'pool type must be ipv4, ipv6, macaddress or string!'), value=pooltype)

        rangesegments = poolrange.replace(' ', '').split(",")
        for rangeseg in rangesegments:
            if '-' in rangeseg:
                (rangestart, rangeend) = rangeseg.replace(' ', '').split("-")
            else:
                continue

            rangestartlen = len(re.split('\.|:',rangestart))
            rangeendlen = len(re.split('\.|:',rangeend))
            if rangestartlen != rangeendlen:
                return dict(result = dict(result=False, value=u'The lengths of start and end or range are different!'), value=poolrange)

            rangestartnum = int(rangestart.encode('utf-8').translate(None, b":.-/ "), 16)
            rangeendnum = int(rangeend.encode('utf-8').translate(None, b":.-/ "), 16)

            if rangestartnum > rangeendnum:
                return dict(result = dict(result=False, value=u'start of range is large than end of range!'), value=poolrange)

        ###################################check the subnet of one range######################################################################
        pl = poolstructure()
        pl.poolSet(poolrange)
        try:
            pl.tostring()
        except:
            #raise ValueError('startaddr and endaddr are not in same subnet')
            return dict(result=False, value=u'startaddr and endaddr are not in same subnet')


        ############ add lock #########################################################################################

        fhandler = _add_lock('almpool', cn)

        try:
            if fhandler:
                result = api.Command['almpool_add_almschema'](
                    cn=u'{0}'.format(cn),
                    almpooltype=u'{0}'.format(pooltype),
                    almrange=u'{0}'.format(poolrange),
                    almstatements=[u'{0}'.format("last created or modified range: " + poolrange)]
                    )
                return dict(result=result['result'], value=cn)
        finally:
            if fhandler:
                _unlock(fhandler)
            else:
                return dict(result=dict(result=False, value=u'other user is locking the pool'), value=cn)

############################################################################################################
@register()
class almpool_mod(Command):
    has_output = output.standard_entry
    __doc__ = _('Modify a new alm pool.')
    msg_summary = _('Modify alm pool "%(value)s"')


    takes_args = (
        Str(
            'cn',
            cli_name='poolname',
            label=_('Poolname'),
            doc=_("Poolname.")
        ),
        Str(
            'almpooltype',
            cli_name='type',
            label=_('Type'),
            doc=_('alm pool type')
        ),
        Str(
            'almrange',
            cli_name='range',
            label=_('Range'),
            doc=_('alm range.')
        ),
        Str(
            'almstatements*',
            cli_name='almstatements',
            label=_('alm Statements'),
            doc=_('alm statements.')
        )
    )

    def execute(self, *args, **kw):
        #logger.info(args)
        #logger.info(kw)
        #logging.info(kw)
        cn = args[0]
        pooltype = args[1]
        poolrange = args[2]
        almstatements = args[3]

        typelist = ['ipv4', 'ipv6', 'macaddress', 'string']

        if pooltype.lower().replace(' ', '') not in typelist:
            return dic(result = dict(result=False, value=u'pool type must be ipv4, ipv6, macaddress or string!'), value=pooltype)

        rangesegments = poolrange.replace(' ', '').split(",")
        for rangeseg in rangesegments:
            if '-' in rangeseg:# exclude string and single value
                (rangestart, rangeend) = rangeseg.replace(' ', '').split("-")
            else:
                continue

            rangestartlen = len(re.split('\.|:',rangestart))
            rangeendlen = len(re.split('\.|:',rangeend))
            if rangestartlen != rangeendlen:
                return dict(result = dict(result=False, value=u'The lengths of start and end or range are different!'), value=poolrange)

            rangestartnum = int(rangestart.encode('utf-8').translate(None, b":.-/ "), 16)
            rangeendnum = int(rangeend.encode('utf-8').translate(None, b":.-/ "), 16)

            if rangestartnum > rangeendnum:
                return dict(result = dict(result=False, value=u'start of range is large than end of range!'), value=poolrange)

        ###################################check the subnet of one range######################################################################
        pl = poolstructure()
        pl.poolSet(poolrange)
        try:
            pl.tostring()
        except:
            return dict(result=False, value=u'startaddr and endaddr are not in same subnet')
        ################################ add lock #############################################################################
        fhandler = _add_lock('almpool', cn)

        try:
            if fhandler:
                result = api.Command['almpool_mod_almschema']( ###lease method use almpool_mod_almschema
                    cn=u'{0}'.format(cn),
                    almpooltype=u'{0}'.format(pooltype),
                    almrange=u'{0}'.format(poolrange),
                    almstatements=[
                        u'{0}'.format("last created or modified range " + poolrange)
                    ]
                )
                return dict(result=result['result'], value=cn)
        finally:
            if fhandler:
                _unlock(fhandler)
            else:
                return dict(result=dict(result=False, value=u'other user is locking the pool'), value=cn)

######################################################
@register()
class almpool_del(Command):
    has_output = output.standard_entry
    __doc__ = _('Delete a alm pool.')
    msg_summary = _('Delete alm pool "%(value)s"')

    takes_args = (
        Str(
            'cn',
            cli_name='cn',
            label=_('Poolname'),
            doc=_("Poolname.")
        )
    )

    def execute(self, *args, **kw):
        cn = args[0]
        ########################## add lock ###################################################################################
        fhandler = _add_lock('almpool', cn)
        try:
            if fhandler:
                #################check leases and make sure no lease belonging to this pool is valid###############################
                resultlease = api.Command['almleases_find']()

                allleasesdict = dict()

                # if resultlease['result'] == []:  # 可能没有lease, indicate that this pool has noot been used.
                #     # unlock
                #     return dict(result=dict(result=False, value=u'No one lease exists. '), value=cn)

                for lease in resultlease['result']:
                    thispoolname = ' '

                    almStatements = lease.get('almstatements', [])

                    for statement in almStatements:
                        if statement.startswith('poolname '):
                            (s, v) = statement.split(' ', 1)
                            thispoolname = v


                    if thispoolname == cn:  # this lease is time-out and belongs to the pool
                        # 完美报错方式，RPC接受this error
                        raise errors.PublicError('Cannot delete this pool: %s ！Because it still has valid address outside!' %cn)
                        #return dict(result=dict(result=False, value=u'this pool still has valid address belonging to valid lease outside. '), value=thispoolname, summary=u'cannot delete this pool')
                ###########################################################################################################

                result = api.Command['almpool_del_almschema']( ###lease method use almpool_mod_almschema
                    cn=u'{0}'.format(cn)
                )
                return dict(result=result['result'], value=cn)
        finally:
            if fhandler:
                _unlock(fhandler)
            else:
                return dict(result=dict(result=False, value=u'other user is locking the pool'), value=cn)
###########################################################################################################


#### almleases ###############################################################

@register()
class almleases(LDAPObject):
    #parent_object = 'almservice'
    container_dn = lease_container_dn
    object_name = _('alm leases')
    object_name_plural = _('alm leasess')
    object_class = ['almleases']
    label = _('alm leasess')
    label_singular = _('alm leases')

    search_attributes = ['cn', 'almaddressstate']
    #search_attributes = ['cn']

    managed_permissions = {
        'System: Add alm leasess': {
            'ipapermright': {'add'},
            'ipapermtargetfilter': ['(objectclass=almleases)'],
            'default_privileges': {'alm Administrators'},
        },
        'System: Modify alm leasess': {
            'ipapermright': {'write'},
            'ipapermtargetfilter': ['(objectclass=almleases)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'almaddressstate',
                'almprimarydn', 'almsecondarydn',
                'almstatements', 'almleasestarttime', 'almoption', 'almcomments',
                'almexpirationtime', 'almstarttimeofstate', 'almlasttransactiontime',
                'almrequestedhostname', 'almassignedhostname', 'almreservedforclient',
                'almassignedtoclient', 'almhwaddress'
            },
            'default_privileges': {'alm Administrators'},
        },
        'System: Remove alm leasess': {
            'ipapermright': {'delete'},
            'ipapermtargetfilter': ['(objectclass=almleases)'],
            'default_privileges': {'alm Administrators'},
        }
    }

    takes_params = (
        Str(
            'cn',
            cli_name='poolnameaddress',
            label=_('alm lease cn'),
            doc=_('alm lease cn.'),
            primary_key=True  # UI plugins's facet will use this.
        ),
        Str(
            'almaddressstate?',
            cli_name='almaddressstate',
            label=_('alm address state'),
            doc=_('alm address state.')
        ),
        Str(
            'almstatements*',
            cli_name='almstatements',
            label=_('alm Statements'),
            doc=_('alm statements.')
        ),
        Str(
            'almleasestarttime?',
            cli_name='almleasestarttime',
            label=_('alm lease start time'),
            doc=_('alm lease start time.')
        ),
        Str(
            'almoption*',
            cli_name='almoptions',
            label=_('alm Options'),
            doc=_('alm options.')
        ),
        Str(
            'almcomments?',
            cli_name='almcomments',
            label=_('Comments'),
            doc=_('alm comments.')
        ),
        Int(
            'defaultleasetime?',
            cli_name='defaultleasetime',
            label=_('Default Lease Time'),
            doc=_('Default lease time.'),
            flags=['virtual_attribute']
        ),
        Int(
            'maxleasetime?',
            cli_name='maxleasetime',
            label=_('Maximum Lease Time'),
            doc=_('Maximum lease time.'),
            flags=['virtual_attribute']
        ),
        Str(
            'almexpirationtime*',
            cli_name='almexpirationtime',
            label=_('alm expiration time'),
            doc=_('alm expiration time.')
        ),
        Str(
            'almstarttimeofstate*',
            cli_name='almstarttimeofstate',
            label=_('alm start time of state'),
            doc=_('alm start time of state.')
        ),
        Str(
            'almlasttransactiontime*',
            cli_name='almlasttransactiontime',
            label=_('alm last transaction time'),
            doc=_('alm last transaction time.')
        ),
        Str(
            'almrequestedhostname*',
            cli_name='almrequestedhostname',
            label=_('alm requested hostname'),
            doc=_('alm requested hostname.')
        ),
        Str(
            'almassignedhostname*',
            cli_name='almassignedhostname',
            label=_('alm assigned hostname'),
            doc=_('alm assigned hostname.')
        ),
        Str(
            'almreservedforclient*',
            cli_name='almreservedforclient',
            label=_('alm reserved for client'),
            doc=_('alm reserved for client.')
        ),
        Str(
            'almassignedtoclient?',
            cli_name='almassignedtoclient',
            label=_('alm assigned to client'),
            doc=_('alm assigned to client.')
        ),
        Str(
            'almhwaddress?',
            cli_name='almhwaddress',
            label=_('alm hwaddress'),
            doc=_('alm hwaddress.')
        ),
    )

    @staticmethod
    def extract_virtual_params(ldap, dn, entry_attrs, keys, options):


        almStatements = entry_attrs.get('almstatements', [])

        for statement in almStatements:
            if statement.startswith('default-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['defaultleasetime'] = v
            if statement.startswith('max-lease-time '):
                (s, v) = statement.split(' ', 1)
                entry_attrs['maxleasetime'] = v

        return entry_attrs


@register()
class almleases_add_almschema(LDAPCreate):
    __doc__ = _('Create a new alm leases.')
    msg_summary = _('Created alm leases "%(value)s"')

    # def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
    #     assert isinstance(dn, DN)
    #
    #     # If the almService entry has almstatements attributes that start with
    #     # "default-lease-time" or "max-lease-time", grab them and copy their
    #     # values into the new leases. This code could probably be a lot more
    #     # efficient, but it works. The blame REALLY lies with the author of the
    #     # alm LDAP schema for being so lazy.
    #
    #     hasDefaultLeaseTime = False
    #     hasMaxLeaseTime = False
    #
    #     if 'almstatements' in entry_attrs:
    #         for statement in entry_attrs['almstatements']:
    #             if statement.startswith('default-lease-time'):
    #                 hasDefaultLeaseTime = True
    #             if statement.startswith('max-lease-time'):
    #                 hasMaxLeaseTime = True
    #
    #     if hasDefaultLeaseTime and hasMaxLeaseTime:
    #         return dn
    #
    #     config = ldap.get_entry(DN(lease_container_dn, api.env.basedn))
    #
    #     if 'almStatements' in config:
    #         configalmStatements = config['almStatements']
    #     else:
    #         configalmStatements = []
    #
    #     defaultLeaseTime = None
    #     maxLeaseTime = None
    #
    #     for statement in configalmStatements:
    #         if statement.startswith('default-lease-time'):
    #             (s, v) = statement.split(" ")
    #             defaultLeaseTime = v
    #         if statement.startswith('max-lease-time'):
    #             (s, v) = statement.split(" ")
    #             maxLeaseTime = v
    #
    #     if 'almstatements' in entry_attrs:
    #         entryalmStatements = entry_attrs['almstatements']
    #     else:
    #         entryalmStatements = []
    #
    #     if defaultLeaseTime is not None:
    #         foundStatement = False
    #         for i, s in enumerate(entryalmStatements):
    #             if s.startswith('default-lease-time'):
    #                 foundStatement = True
    #                 #entryalmStatements[i] = 'default-lease-time {0}'.format(defaultLeaseTime)
    #                 entryalmStatements[i] = s
    #                 break
    #         if foundStatement is False:
    #             entryalmStatements.append('default-lease-time {0}'.format(defaultLeaseTime))
    #
    #     if maxLeaseTime is not None:
    #         foundStatement = False
    #         for i, s in enumerate(entryalmStatements):
    #             if s.startswith('max-lease-time'):
    #                 foundStatement = True
    #                 #entryalmStatements[i] = 'max-lease-time {0}'.format(maxLeaseTime)
    #                 entryalmStatements[i] = s
    #                 break
    #         if foundStatement is False:
    #             entryalmStatements.append('max-lease-time {0}'.format(maxLeaseTime))
    #
    #     entry_attrs['almstatements'] = entryalmStatements
    #
    #     return dn


@register()
class almleases_find(LDAPSearch):
    __doc__ = _('Search for a alm leases.')
    msg_summary = ngettext(
        '%(count)d alm leases matched',
        '%(count)d alm leasess matched', 0
    )


@register()
class almleases_show(LDAPRetrieve):
    __doc__ = _('Display a alm leases.')

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = almleases.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn


@register()
class almleases_mod_almschema(LDAPUpdate):
    __doc__ = _('Modify a alm leases.')
    msg_summary = _('Modified a alm leases.')

    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)
        return dn
    #
    #     entry = ldap.get_entry(dn)
    #
    #
    #     if 'almstatements' in entry_attrs:
    #         almStatements = entry_attrs.get('almstatements', [])
    #     else:
    #         almStatements = entry.get('almstatements', [])
    #
    #     if 'defaultleasetime' in options:
    #         statement = 'default-lease-time {0}'.format(options['defaultleasetime'])
    #         foundStatement = False
    #         for i, s in enumerate(almStatements):
    #             if s.startswith('default-lease-time '):
    #                 foundStatement = True
    #                 almStatements[i] = statement
    #                 break
    #         if not foundStatement:
    #             almStatements.append(statement)
    #
    #     if 'maxleasetime' in options:
    #         statement = 'max-lease-time {0}'.format(options['maxleasetime'])
    #         foundStatement = False
    #         for i, s in enumerate(almStatements):
    #             if s.startswith('max-lease-time '):
    #                 foundStatement = True
    #                 almStatements[i] = statement
    #                 break
    #         if not foundStatement:
    #             almStatements.append(statement)
    #
    #     entry_attrs['almstatements'] = almStatements
    #
    #     if 'almoption' in entry_attrs:
    #         almOptions = entry_attrs.get('almoption', [])
    #     else:
    #         almOptions = entry.get('almoption', [])
    #
    #     entry_attrs['almoption'] = almOptions
    #
    #     return dn

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        entry_attrs = almleases.extract_virtual_params(ldap, dn, entry_attrs, keys, options)
        return dn



    @lockdecorator
    def execute(self, *keys, **options):
        result = super(self.__class__, self).execute(*keys, **options)
        return result




@register()
class almleases_mod_nolock(LDAPUpdate):
    __doc__ = _('Modify a alm leases no lock.')
    msg_summary = _('Modified a alm leases no lock.')

@register()
class almleases_del_almschema(LDAPDelete):
    __doc__ = _('Delete a alm leases.')
    msg_summary = _('Deleted alm leases "%(value)s"')



############################################add pattern error to mod_pool
@register()
class almleases_add(Command):
    has_output = output.standard_entry
    __doc__ = _('Create a new alm lease.')
    msg_summary = _('Created alm lease "%(value)s"')

    takes_args = (
        Str(
            'cn',
            cli_name='poolnameaddress',
            label=_('alm lease cn'),
            doc=_('alm lease cn.'),
            primary_key=True
        ),
        Str(
            'almaddressstate?',
            cli_name='almaddressstate',
            label=_('alm address state'),
            doc=_('alm address state.')
        ),
        Str(
            'almleasestarttime?',
            cli_name='almleasestarttime',
            label=_('alm lease start time'),
            doc=_('alm lease start time.')
        ),
        Str(
            'almstatements*',
            cli_name='almstatements',
            label=_('alm Statements'),
            doc=_('alm statements.')
        )
    )

    def execute(self, *args, **kw):
        cn = args[0]
        leasestate = args[1] if len(args) >= 2 else u'leased'
        starttime = args[2] if len(args) >= 3 else u'{0}'.format(int(time.time()))
        statements = args[3] if len(args) >= 4 else None

#############################################################################################################
        #string_tabtrans = str(cn).maketrans('-./', '___')
        fhandler = _add_lock('almleases', cn)

        try:
            if fhandler:
                result = api.Command['almleases_add_almschema'](
                    cn=u'{0}'.format(cn),
                    almaddressstate=u'{0}'.format(leasestate),
                    almleasestarttime=u'{0}'.format(starttime),
                    almstatements=statements
                )
                return dict(result=result['result'], value=cn)
        finally:
            if fhandler:
                _unlock(fhandler)
            else:
                return dict(result=dict(result=False, value=u'other user is locking this lease'), value=cn)

#####################################################################################


@register()
class almleases_mod(Command):
    has_output = output.standard_entry
    __doc__ = _('Modify a alm lease.')
    msg_summary = _('Modify alm lease "%(value)s"')

    takes_options = (
        Str(
            'cn',
            cli_name='poolnameaddress',
            label=_('alm lease cn'),
            doc=_('alm lease cn.'),
            primary_key=True
        ),
        Str(
            'almaddressstate?',
            cli_name='almaddressstate',
            label=_('alm address state'),
            doc=_('alm address state.')
        ),
        Str(
            'almleasestarttime?',
            cli_name='almleasestarttime',
            label=_('alm lease start time'),
            doc=_('alm lease start time.')
        ),
        Str(
            'almstatements*',
            cli_name='almstatements',
            label=_('alm Statements'),
            doc=_('alm statements.')
        ),
    )

    def execute(self, *args, **kw):
        # logging.warning("args are: ")
        # logging.warning(args)
        logging.warning("kws are: ")
        logging.warning(kw)
        cn = u'cn'
        leasestate = u'leased'
        starttime = u'{0}'.format(int(time.time()))
        statements = None

        if 'cn' in kw:
            cn = kw.get('cn')
        if 'almaddressstate' in kw:
            leasestate = kw.get('almaddressstate')
        if 'almleasestarttime' in kw:
            starttime = kw.get('almleasestarttime')
        if 'almstatement' in kw:
            statements = kw.get('almstatement')


        #############################################################################################################
        fhandler = _add_lock('almleases', cn)
        try:
            if fhandler:
                result = api.Command['almleases_mod_nolock'](
                    cn=u'{0}'.format(cn),
                    almaddressstate=u'{0}'.format(leasestate),
                    almleasestarttime=u'{0}'.format(starttime),
                    almstatements=statements
                )
                return dict(result=result['result'], value=cn)
        finally:
            if fhandler:
                _unlock(fhandler)
            else:
                return dict(result=dict(result=False, value=u'other user is locking this lease'), value=cn)

#####################################################################################

@register()
class almleases_del(Command):
    has_output = output.standard_entry
    __doc__ = _('Delete a alm lease.')
    msg_summary = _('Delete alm lease "%(value)s"')

    takes_args = (
        Str(
            'cn',
            cli_name='poolnameaddress',
            label=_('alm lease cn'),
            doc=_('alm lease cn.'),
            primary_key=True
        )
    )

    def execute(self, *args, **kw):
        cn = args[0]

        ############################ add lock #################################################################################
        fhandler = _add_lock('almleases', cn)
        try:
            if fhandler:
                result = api.Command['almleases_del_almschema'](
                    cn=u'{0}'.format(cn)
                )
                return dict(result=result['result'], value=cn)
        finally:
            if fhandler:
                _unlock(fhandler)
            else:
                return dict(result=dict(result=False, value=u'other user is locking this lease'), value=cn)

###########################################################################################################


#### almhost #################################################################


@register()
class almhost(LDAPObject):
    container_dn = containerdn
    object_name = _('alm host')
    object_name_plural = _('alm hosts')
    object_class = ['almhost']
    label = _('alm Hosts')
    label_singular = _('alm Host')

    search_attributes = [ 'cn', 'almhwaddress' ]

    managed_permissions = {
        'System: Add alm Hosts': {
            'ipapermright': {'add'},
            'ipapermtargetfilter': ['(objectclass=almhost)'],
            'default_privileges': {'alm Administrators', 'Host Administrators'},
        },
        'System: Modify alm Hosts': {
            'ipapermright': {'write'},
            'ipapermtargetfilter': ['(objectclass=almhost)'],
            'ipapermdefaultattr': {
                'cn', 'objectclass',
                'almhwaddress',
                'almstatements', 'almoption', 'almcomments'
            },
            'default_privileges': {'alm Administrators', 'Host Administrators'},
        },
        'System: Remove alm Hosts': {
            'ipapermright': {'delete'},
            'ipapermtargetfilter': ['(objectclass=almhost)'],
            'default_privileges': {'alm Administrators', 'Host Administrators'},
        }
    }

    takes_params = (
        Str(
            'cn',
            cli_name='cn',
            label=_('Canonical Name'),
            doc=_('Canonical name.'),
            primary_key=True
        ),
        Str(
            'almhwaddress',
            cli_name='almhwaddress',
            label=('alm Hardware Address'),
            doc=_('alm hardware address.')
        ),
        Str(
            'almstatements*',
            cli_name='almstatements',
            label=_('alm Statements'),
            doc=_('alm statements.')
        ),
        Str(
            'almoption*',
            cli_name='almoptions',
            label=_('alm Options'),
            doc=_('alm options.')
        ),
        Str(
            'almcomments?',
            cli_name='almcomments',
            label=_('Comments'),
            doc=_('alm comments.')
        )
    )


@register()
class almhost_add_almschema(LDAPCreate):
    NO_CLI = True
    __doc__ = _('Create a new alm host.')
    msg_summary = _('Created alm host "%(value)s"')


@register()
class almhost_find(LDAPSearch):
    __doc__ = _('Search for a alm host.')
    msg_summary = ngettext(
        '%(count)d alm host matched',
        '%(count)d alm hosts matched', 0
    )


@register()
class almhost_show(LDAPRetrieve):
    __doc__ = _('Display a alm host.')


@register()
class almhost_del_almschema(LDAPDelete):
    NO_CLI = True
    __doc__ = _('Delete a alm host.')
    msg_summary = _('Deleted alm host "%(value)s"')


@register()
class almhost_add(Command):
    has_output = output.standard_entry
    __doc__ = _('Create a new alm host.')
    msg_summary = _('Created alm host "%(value)s"')

    takes_args = (
        Str(
            'hostname',
            cli_name='hostname',
            label=_('Hostname'),
            doc=_("Hostname.")
        ),
        Str(
            'macaddress',
            normalizer=lambda value: value.upper(),
            pattern='^([a-fA-F0-9]{2}[:|\-]?){5}[a-fA-F0-9]{2}$',
            pattern_errmsg=('Must be of the form HH:HH:HH:HH:HH:HH, where '
                            'each H is a hexadecimal character.'),
            cli_name='macaddress',
            label=_('MAC Address'),
            doc=_("MAC address.")
        )
    )

    def execute(self, *args, **kw):
        hostname = args[0]
        macaddress = args[1]
        cn = u'{hostname}-{macaddress}'.format(
            hostname=hostname,
            macaddress=macaddress.replace(':', '')
        )
        result = api.Command['almhost_add_almschema'](
            cn,
            almhwaddress=u'ethernet {0}'.format(macaddress),
            almstatements=[u'fixed-address {0}'.format(hostname)],
            almoption=[u'host-name "{0}"'.format(hostname)]
        )
        return dict(result=result['result'], value=result['value'])


@register()
class almhost_del(Command):
    has_output = output.standard_entry
    __doc__ = _('Delete a alm host.')
    msg_summary = _('Deleted alm host "%(value)s"')

    takes_args = (
        Str(
            'hostname',
            cli_name='hostname',
            label=_('Hostname'),
            doc=_("Hostname.")
        ),
        Str(
            'macaddress',
            normalizer=lambda value: value.upper(),
            pattern='^([a-fA-F0-9]{2}[:|\-]?){5}[a-fA-F0-9]{2}$',
            pattern_errmsg=('Must be of the form HH:HH:HH:HH:HH:HH, where '
                            'each H is a hexadecimal character.'),
            cli_name='macaddress',
            label=_('MAC Address'),
            doc=_("MAC address.")
        )
    )

    def execute(self, *args, **kw):
        hostname = args[0]
        macaddress = args[1]
        cn = u'{hostname}-{macaddress}'.format(
            hostname=hostname,
            macaddress=macaddress.replace(':', '')
        )
        result = api.Command['almhost_del_almschema'](cn)
        return dict(result=result['result'], value=cn)


###############################################################################


from . import host


def host_add_almhost(self, ldap, dn, entry_attrs, *keys, **options):
    if 'macaddress' in entry_attrs:
        for addr in entry_attrs['macaddress']:
            api.Command['almhost_add'](entry_attrs['fqdn'][0], addr)
    return dn

host.host_add.register_post_callback(host_add_almhost)


def host_mod_almhost(self, ldap, dn, entry_attrs, *keys, **options):
    if 'macaddress' not in options:
        return dn

    if options['macaddress'] is None:
        macaddresses = []
    else:
        macaddresses = list(options['macaddress'])

    filter = ldap.make_filter(
        {
            'cn': entry_attrs['fqdn'][0]
        },
        exact=False,
        leading_wildcard=False,
        trailing_wildcard=True
    )

    entries = []
    try:
        entries = ldap.get_entries(
            DN(containerdn, api.env.basedn),
            ldap.SCOPE_SUBTREE,
            filter
        )
    except errors.NotFound:
        pass

    for entry in entries:
        entry_macaddr = entry['almHWAddress'][0].replace('ethernet ', '')
        if entry_macaddr not in macaddresses:
            api.Command['almhost_del'](entry_attrs['fqdn'][0], entry_macaddr)
        if entry_macaddr in macaddresses:
            macaddresses.remove(entry_macaddr)

    for new_macaddr in macaddresses:
        api.Command['almhost_add'](entry_attrs['fqdn'][0], new_macaddr)

    return dn

host.host_mod.register_post_callback(host_mod_almhost)


def host_del_almhost(self, ldap, dn, *keys, **options):

    entry = ldap.get_entry(dn)

    if 'macaddress' in entry:
        for addr in entry['macaddress']:
            try:
                api.Command['almhost_del'](entry['fqdn'][0], addr)
            except:
                pass

    return dn

host.host_del.register_pre_callback(host_del_almhost)

###create lease###################
@register()
class alm_lease(Command):
    has_output = output.standard_entry
    __doc__ = _('create a alm lease.')

    takes_options = (
    #takes_args = (
        Str(
            'clientid',
            cli_name='clientid',
            label=_('ClientID'),
            doc=_("ClientID.")
        ),
        Str(
            'poolname',
            cli_name='poolname',
            label=_('Poolname'),
            doc=_("Poolname.")
        ),
        Str(
            'almpooltype',
            pattern='ipv4|ipv6|macaddress|string',
            pattern_errmsg=('Must be one of ipv4, ipv6, macaddress or string.'),
            cli_name='type',
            label=_('Type'),
            doc=_('alm pool type')
        ),
        Str(
            'expires?',
            # pattern='^((25[0-5]|2[0-4]\\d|[1]{1}\\d{1}\\d{1}|[1-9]{1}\\d{1}|\\d{1})($|(?!\\.$)\\.)){4}$',
            # pattern_errmsg=('Must be proper formate of IPv4.'),
            cli_name='expires',
            label=_('lease expires'),
            doc=_('Lease Expires.'),
        ),
        Str(
            'requiredaddress?',
            #pattern='^((25[0-5]|2[0-4]\\d|[1]{1}\\d{1}\\d{1}|[1-9]{1}\\d{1}|\\d{1})($|(?!\\.$)\\.)){4}$',
            #pattern_errmsg=('Must be proper formate of IPv4.'),
            cli_name='requiredaddr',
            label=_('RequiredAddr'),
            doc=_('Required Address.'),
        ),
    )


    def execute(self, *args, **kw):
        logging.warning(args)
        logging.warning(kw)
        clientid = 'clientid'
        poolname = 'poolname'
        pooltype = 'pooltype'
        expiretime = u'{0}'.format(int(time.time()) + 31536000)
        requiredaddr = 'default'


        if 'clientid' in kw:
            clientid = kw.get('clientid')
        if 'poolname' in kw:
            poolname = kw.get('poolname')
        if 'almpooltype' in kw:
            almpooltype = kw.get('almpooltype')
        if 'expires' in kw:
            expiretime = kw.get('expires')
        if 'requiredaddress' in kw:
            requiredaddr = kw.get('requiredaddress')


        # clientid = args[0]
        # poolname = args[1]
        # pooltype = args[2]
        # expireTemp = args[3] if len(args) >= 4 else u'{0}'.format(int(time.time()) + 31536000)
        # addrTemp = args[4] if len(args) >= 4 else 'default'
        #
        # logging.warning(args)
        # logging.warning(expireTemp.isdigit())
        #
        # if expireTemp.isdigit():
        #     expiretime = expireTemp
        #     requiredaddr = addrTemp
        # else:
        #     requiredaddr = expireTemp
        #     expiretime = addrTemp if addrTemp.isdigit() else u'{0}'.format(int(time.time()) + 31536000)


        ######two types of expires: absolute time, + duration time#################################################################
        if '+' in expiretime:
            expiretime = u'{0}'.format(int(expiretime.replace(" ", "").split("+")[1]) + int(time.time()))

        ################################ add lock #############################################################################

        fhandlerPool = _add_lock('almpool', poolname)


        try:
            if fhandlerPool:
                logging.warning("have locked pool : %s ", poolname)
                ######################check the pool#######################################################################################
                cn = u'{0}'.format(poolname)
                resultpoolshow = api.Command['almpool_show'](cn)

                if resultpoolshow['result'] == []:  # 可能没有this pool
                    # unlock
                    return dict(result=dict(result=False, value=u'This pool does not exist. '), value=poolname)

                almrange = resultpoolshow['result']['almrange']

                ####   clear time-out lease    ###
                if almrange[0] == 'Empty':
                    ########################iterate all leases and collect time-out leases###############################################
                    resultlease = api.Command['almleases_find']()

                    freeaddrdict = dict()
                    # return dict(result=resultlease['result'], value=resultlease['summary'])

                    if resultlease['result'] == []:  # 可能没有lease
                        # unlock
                        return dict(result=dict(result=False, value=u'No one lease exists. '), value=poolname)

                    for lease in resultlease['result']:
                        expires = ' '
                        thispoolname = ' '
                        leasedaddr = ' '

                        for statement in lease['almstatements']:
                            if statement.startswith('expires '):
                                (s, v) = statement.split(' ', 1)
                                expires = v
                            if statement.startswith('poolname '):
                                (s, v) = statement.split(' ', 1)
                                thispoolname = v
                            if statement.startswith('leasedaddr '):
                                (s, v) = statement.split(' ', 1)
                                leasedaddr = v

                        if int(time.time()) > int(
                                expires) and thispoolname == thispoolname:  # this lease is time-out and belongs to the pool
                            ###################collect and classify addr and poolname#############################################################
                            if freeaddrdict.get(thispoolname) is None:
                                freeaddrdict[thispoolname] = [leasedaddr]
                            else:
                                freeaddrdict[thispoolname].append(leasedaddr)

                            ###################delete this lease##################################################################################
                            try:
                                resultlease_del = api.Command['almleases_del'](lease['cn'])  # 前面读lease，已经检测如果没lease，直接跳出，这里不需要再检测了。
                            except:
                                pass

                    ###################return this addr back to pool##########################################################################
                    for pool in freeaddrdict:  # 如果没有lease过期，后续操作不会进行。
                        ###################################read pool######################################################################
                        cn = u'{0}'.format(pool)
                        resultpoolshow = api.Command['almpool_show'](cn)  # 前面读pool, lease已经做过检测，这里必定有pool
                        almrange = resultpoolshow['result']['almrange']
                        if almrange[0] == 'Empty':
                            almrange[0] = ''

                        # pl = Trie()
                        pl = poolstructure()
                        pl.poolSet(almrange[0])
                        for addr in freeaddrdict[pool]:
                            pl.insert(addr)
                        #   mod the pool    #######################################################
                        # modRange = pl.beString(pooltype)
                        modRange = pl.tostring()
                        cn = u'{0}'.format(pool)
                        resultpoolmod = api.Command['almpool_mod_nolock'](  # 可能没有lease过期，这里可能不会mod pool
                            cn,
                            almpooltype=u'{0}'.format(pooltype),
                            almrange=u'{0}'.format(modRange)
                        )

                    #####   check pool again####################################################################################
                    cn = u'{0}'.format(poolname)
                    resultpoolshow = api.Command['almpool_show'](cn)  # 前面读pool, lease已经做过检测，这里必定有pool
                    almrange = resultpoolshow['result']['almrange']

                if almrange[0] == 'Empty':
                    # unlock
                    raise errors.NotFound(
                        reason=_(
                            "After setting free time-out leases, the pool is still empty. Please check out addr from other pools"))
                    # return dict(result=dict(result=False, value=u'all'), value=getaddr)

                # after checking the pool and make sure it is not empty

                pool = poolstructure()
                pool.poolSet(almrange[0])  # 注意在add pool并添加range的时候，range可以是192.1-192.10 或 192.1 192.10，要统一格式。

                logging.warning("requiredaddr : %s ", requiredaddr)
                if pool.search(requiredaddr):
                    getaddr = requiredaddr
                else:
                    getaddr = pool.getRandom()  # automatically delete this Randomly gotten node
                logging.warning("getaddr : %s ", getaddr)
                deletepool = pool.delete(getaddr)

                if getaddr == '':
                    # it never happen because this pool is locked by this lease commmand, just in case.
                    return dict(result=dict(result=False, value=u'pool is empty and getaddr is ''.'), value=getaddr)
                #  create a lease     ##########################

                cnleaseadd = u'{0}'.format(poolname + '-' + getaddr)
                logging.warning("ready to add a lease : %s ", cnleaseadd)
                resultleaseadd = api.Command['almleases_add'](
                    cnleaseadd,
                    almaddressstate=u'leased',
                    almleasestarttime=u'{0}'.format(int(time.time())),
                    almstatements=[
                        u'{0}'.format("clientid " + clientid),
                        u'{0}'.format("poolname " + poolname),
                        u'{0}'.format("almpooltype " + pooltype),
                        u'{0}'.format("leasedaddr " + getaddr),
                        u'{0}'.format("expires " + expiretime)
                    ]

                )
                #第一个写操作：lease_add，如果失败不需要撤销任何步骤，直接跳到finally执行解锁
                #api.Command如果执行失败就直接跳出
                modRange = pool.tostring()
                if modRange == '':
                    modRange = 'Empty'

                try:
                    cn = u'{0}'.format(poolname)
                    resultpoolmod2 = api.Command['almpool_mod_nolock'](
                        cn,
                        almpooltype=u'{0}'.format(pooltype),
                        almrange=u'{0}'.format(modRange)
                    )
                    return dict(result=resultleaseadd['result'], value=u'successfully lease!')
                #第二个写操作：pool_mod，如果失败，就撤销lease_add，return错误信息，然后跳到finally执行解锁
                except:
                    resultrevokeleaseadd = api.Command['almleases_del'](cnleaseadd)
                    return dict(result=dict(result=False, value=u'cannot allocate a lease from this pool'), value=poolname)

        finally:
            if fhandlerPool:
                _unlock(fhandlerPool)
            else:
                return dict(result=dict(result=False, value=u'other user is locking the pool'), value=poolname)





###release###################
@register()
class alm_release(Command):
    has_output = output.standard_entry
    __doc__ = _('revoke/release a alm lease.')


    takes_options = (
        Str(
            'clientid',
            cli_name='clientid',
            label=_('ClientID'),
            doc=_("ClientID.")
        ),
        Str(
            'poolname',
            cli_name='poolname',
            label=_('Poolname'),
            doc=_("Poolname.")
        ),
        Str(
            'almpooltype',
            pattern='ipv4|ipv6|macaddress|string',
            pattern_errmsg=('Must be one of ipv4, ipv6, macaddress or string.'),
            cli_name='type',
            label=_('Type'),
            doc=_('alm pool type')
        ),
        Str(
            'leasedaddress',
            cli_name='leasedaddress',
            label=_('Leased Address'),
            doc=_('Leased Address.'),
        ),
    )


    def execute(self, *args, **kw):
        logging.error(args)
        logging.error(kw)

        clientid = u'clientid'
        poolname = u'poolname'
        pooltype = u'pooltype'
        leasedaddr = u'default'

        if 'clientid' in kw:
            clientid = kw.get('clientid')
        if 'poolname' in kw:
            poolname = kw.get('poolname')
        if 'almpooltype' in kw:
            pooltype = kw.get('almpooltype')
        if 'leasedaddress' in kw:
            leasedaddr = kw.get('leasedaddress')

        leasecn = u'{0}'.format(poolname + '-' + leasedaddr)
        thispool = poolname
        ###    add      ##########################################################################################################
        fhandler1 = _add_lock('almpool', poolname) #   add lock on the pool
        fhandler2 = _add_lock('almpool', 'deleted_pool')#  if the pool doesnt exist, we have to create a pool to store set-free leases
        fhandler3 = _add_lock('almleases', leasecn)  # add lock on the pool
        resultleasedeleted = None
        result = None
        try:
            logging.warning("starting release")
            if fhandler1 and fhandler2 and fhandler3:
                logging.warning("successfully add three lock files")
                ###   search lease    ###
                cn = u'{0}'.format(poolname + '-' + leasedaddr)

                try:
                    result = api.Command['almleases_show'](cn)
                except :#Exception as err:
                    logging.warning("Cannot find this lease")
                    raise errors.PublicError(
                    'Cannot find this lease: %s ！Please check poolname!' % cn)

                logging.warning("has throwed a exception")
                for statement in result['result']['almstatements']:
                    if statement.startswith('expires '):
                        (s, v) = statement.split(' ', 1)
                        expires = v

                ###    如果lease_show失败，直接跳出
                logging.warning(cn)
                resultleasedeleted = api.Command['almleases_del_almschema'](cn)
                logging.warning("almleases has been deleted")

                ###    read pool    ###
                try:
                    cn = u'{0}'.format(poolname)
                    result = api.Command['almpool_show'](cn)

                ###    edge case: create a lease, then delete the pool, then revoke the lease     ###
                # pool_mod fail.

                except:
                    try:
                        cn = u'deleted_pool'
                        result = api.Command['almpool_show'](cn)
                        poolname = cn
                    except:
                        cn = u'deleted_pool'
                        ###    如果add失败    已经删除了lease，没有pool存它   ###
                        result = api.Command['almpool_add_almschema'](
                            cn,
                            almpooltype=u'{0}'.format(pooltype),
                            almrange=u'{0}'.format('Empty'),
                            almstatements = [
                            u'{0}'.format("last created or modified range: " + 'Empty')]
                        )

                        result = api.Command['almpool_show'](cn)
                        poolname = cn

                almrange = result['result']['almrange']
                if almrange[0] == 'Empty':
                    almrange[0] = ''

                pool = poolstructure()
                pool.poolSet(almrange[0])  # 注意在add pool并添加range的时候，range可以是192.1-192.10 或 192.1 192.10，要统一格式。
                pool.insert(leasedaddr)

                modRange = pool.tostring()


                cn = u'{0}'.format(poolname)
                result = api.Command['almpool_mod_nolock'](
                    cn,
                    almpooltype=u'{0}'.format(pooltype),
                    almrange=u'{0}'.format(modRange)
                )
                return dict(result=result['result'], value=u'successfully release!')
        except Exception as err:
            logging.warning("catch a exception and recover lease")
            #     如果在删除lease后，后续操作有error，就还原已删除的lease
            logging.warning(resultleasedeleted)
            if resultleasedeleted is not None:
                resultleaseadd = api.Command['almleases_add_almschema'](
                    leasecn,
                    almaddressstate=u'leased',
                    almleasestarttime=u'{0}'.format(int(time.time())),
                    almstatements=[
                        u'{0}'.format("poolname " + thispool),
                        u'{0}'.format("leasedaddr " + leasedaddr),
                        u'{0}'.format("expires " + expires),
                        u'{0}'.format("clientID " + clientid)
                    ]
                )
            else:
                raise errors.PublicError(
                    'Cannot find this lease: %s ！Please check poolname!' % leasecn)


            return dict(result=dict(result=False, value=u'{0}'.format(err)), value=cn)




        finally:
            if fhandler1 and fhandler2 and fhandler3:
                _unlock(fhandler1)
                _unlock(fhandler2)
                _unlock(fhandler3)
            elif fhandler1:
                _unlock(fhandler1)
                return dict(result=dict(result=False, value=u'cannot lock deleted_pool or lease'), value=cn)
            elif fhandler2:
                _unlock(fhandler2)
                return dict(result=dict(result=False, value=u'cannot lock pool or lease'), value=cn)
            elif fhandler3:
                _unlock(fhandler3)
                return dict(result=dict(result=False, value=u'cannot lock pool or deleted_pool'), value=cn)
            else:
                return dict(result=dict(result=False, value=u'cannot lock pool, deleted_pool and lease'), value=cn)


