#!/usr/bin/env python
# _*_ coding:utf-8 _*_
"""
comments
"""
from netaddr import *
import random
import re

class poolstructure:
    def __init__(self):
        self.pool = ''
        self.startaddr = list()
        self.endaddr = list()

    def poolSet(self, addrrange):#input from LDAP #support ipv6
        #self.poolrange = addrrange
        startaddr = list()
        endaddr = list()
        segments = addrrange.replace(' ', '').split(',') ##### if addrange = '' : startaddr = endaddr = ['']##############
        for seg in segments:
            startend = seg.split('-')
            if len(startend) == 1:
                startaddr.append(startend[0])
                endaddr.append(startend[0])
            elif len(startend) == 2:
                startraw = startend[0]
                endraw = startend[1]
                startrawlist = startraw.split('/')
                endrawlist = endraw.split('/')
                if len(startrawlist) > len(endrawlist):
                    endraw = endraw + '/' + startrawlist[1]
                elif len(endrawlist) > len(startrawlist):
                    startraw = startraw + '/' + endrawlist[1]

                startaddr.append(startraw)
                endaddr.append(endraw)
        self.startaddr = startaddr
        self.endaddr = endaddr

    def insert(self, addr): #when inserting one addr, we need to check relationships of subnet
        addr = addr.replace(' ', '') # assuming startaddr and endaddr are in same subnet
        addrtype = self.decttype(addr)
        if addrtype != 'string':
            for i in range(0, len(self.startaddr)):
                startaddrtype = self.decttype(self.startaddr[i])
                if addrtype == startaddrtype: #exclude string
                    addrval = self.addr2int(addr)
                    startval = self.addr2int(self.startaddr[i])
                    endval = self.addr2int(self.endaddr[i])
                    if addrtype != 'macaddr': #ipv4 or ipv6
                        curaddrnetwork = IPNetwork(addr).network
                        startaddrnetwork = IPNetwork(self.startaddr[i]).network
                        endaddrnetwork = IPNetwork(self.endaddr[i]).network
                        if i + 1 < len(self.startaddr) and self.decttype(self.startaddr[i + 1]) == addrtype:
                            nextstartaddrnetwork = IPNetwork(self.startaddr[i + 1]).network

                    else:
                        curaddrnetwork = 'macaddrnetwork'
                        startaddrnetwork = curaddrnetwork
                        endaddrnetwork = curaddrnetwork
                        nextstartaddrnetwork = curaddrnetwork


                    if addrval >= startval and addrval <= endval and curaddrnetwork == startaddrnetwork: # in this range
                        return
                    elif addrval == startval - 1 and curaddrnetwork == startaddrnetwork: #expand start
                        self.startaddr[i] = addr
                        return
                    elif addrval == endval + 1: #expand end
                        if i + 1 < len(self.startaddr):
                            if addrval == self.addr2int(self.startaddr[i + 1]) - 1 and curaddrnetwork == startaddrnetwork and curaddrnetwork == nextstartaddrnetwork: #merge two range
                                self.startaddr.pop(i + 1)
                                self.endaddr.pop(i)
                                return
                            else:
                                self.endaddr[i] = addr
                                return
                        elif curaddrnetwork == startaddrnetwork:
                            self.endaddr[i] = addr
                            return
        #string or addrs do not belong to orignal range
        self.startaddr.append(addr)
        self.endaddr.append(addr)


    def addr2int(self, addr):
        addrtype = self.decttype(addr)
        if addrtype == 'ipv4' or addrtype == 'ipv6':
            intval = IPNetwork(addr).value
        elif addrtype == 'macaddr':
            intval = int(addr.encode('utf-8').translate(None, b":.- "), 16)
        else:
            raise TypeError('not a ipv4, ipv6 or macaddress')
        return intval

    def search(self, addr): #insert single one node
        addr = addr.replace(' ', '')
        if self.decttype(addr) != 'string':
            for i in range(0, len(self.startaddr)):
                if self.decttype(addr) == self.decttype(self.startaddr[i]):
                    addrval = self.addr2int(addr)
                    startval = self.addr2int(self.startaddr[i])
                    endval = self.addr2int(self.endaddr[i])

                    if addrval >= startval and addrval <= endval:
                        return True

        else:# addr is string
            for address in self.startaddr:
                if addr == address:
                    return True

        return False



    def delete(self, addr): #assuming startaddr[i] and endaddr[i] are in same subnet
        addr = addr.replace(' ', '')
        if self.decttype(addr) != 'string':
            for i in range(0, len(self.startaddr)):
                if self.decttype(addr) == self.decttype(self.startaddr[i]):
                    addrval = self.addr2int(addr)
                    startval = self.addr2int(self.startaddr[i])
                    endval = self.addr2int(self.endaddr[i])

                    if addrval == startval:# at start
                        if startval == endval:#single addr
                            self.startaddr.pop(i)
                            self.endaddr.pop(i)
                            return
                        else:#at least two value range
                            self.startaddr[i] = self.movaddr(addr, 1)
                            return
                    elif addrval > startval and addrval < endval:#between start and end, separate this range
                        self.startaddr.insert(i + 1, self.movaddr(addr, 1)) if i + 1 < len(self.startaddr) else self.startaddr.append(self.movaddr(addr, 1))
                        self.endaddr.insert(i, self.movaddr(addr, -1))
                    elif addrval == endval:#at lease two value range, coz we have dealt with single value when addrval == startval
                        self.endaddr[i] = self.movaddr(addr, -1)

        else:  # addr is string
            for i in range(0, len(self.startaddr)):
                if addr == self.startaddr[i]:
                    self.startaddr.pop(i)
                    self.endaddr.pop(i)
                    return

    def movaddr(self, addr, num):
        addrtype = self.decttype(addr)
        if addrtype == 'ipv4' or addrtype == 'ipv6':
            curaddr = IPNetwork(addr)
            prefix = curaddr.prefixlen
            curval = curaddr.value
            newval = curval + num
            newaddr = str(IPAddress(newval)) + '/' + str(prefix)
            if IPNetwork(newaddr).ip < curaddr[0] or IPNetwork(newaddr).ip > curaddr[-1]:
                raise ValueError('this ip doesnt belong to this network, cannot operate')

        elif addrtype == 'macaddr':
            curval = int(addr.encode('utf-8').translate(None, b":.- "), 16)
            newval = curval + num
            mac_hex = "{:012x}".format(newval)
            newaddr = ":".join(
                mac_hex[i:i + 2] for i in range(0, len(mac_hex), 2))  # convert mac_int into mac_str
        else:
            raise TypeError('not a ipv4, ipv6 or macaddress')
        return newaddr



    def decttype(self, addr):
        addr = addr.replace(' ', '')
        if re.match(r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(/(3[0-2]|[0-2]?\d))?$', addr):
            return 'ipv4'
        elif re.match(r'^([a-fA-F0-9]{2}[:|\-]?){5}[a-fA-F0-9]{2}$', addr):
            return 'macaddr'
        elif re.match(
                r'^([\da-fA-F]{1,4}:){6}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^::([\da-fA-F]{1,4}:){0,4}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^([\da-fA-F]{1,4}:):([\da-fA-F]{1,4}:){0,3}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^([\da-fA-F]{1,4}:){2}:([\da-fA-F]{1,4}:){0,2}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^([\da-fA-F]{1,4}:){3}:([\da-fA-F]{1,4}:){0,1}((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^([\da-fA-F]{1,4}:){4}:((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^([\da-fA-F]{1,4}:){7}[\da-fA-F]{1,4}(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^:((:[\da-fA-F]{1,4}){1,6}|:)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^[\da-fA-F]{1,4}:((:[\da-fA-F]{1,4}){1,5}|:)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^([\da-fA-F]{1,4}:){2}((:[\da-fA-F]{1,4}){1,4}|:)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^([\da-fA-F]{1,4}:){3}((:[\da-fA-F]{1,4}){1,3}|:)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^([\da-fA-F]{1,4}:){4}((:[\da-fA-F]{1,4}){1,2}|:)(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^([\da-fA-F]{1,4}:){5}:([\da-fA-F]{1,4})?(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$|^([\da-fA-F]{1,4}:){6}:(/(12[0-8]|1[0-1]\d|[0]?\d\d?))?$',
                addr):
            return 'ipv6'
        else:
            return 'string'



    def tostring(self): # Output from LDAP
        ans = ''
        for i in range(0, len(self.startaddr)):
            startaddrtype = self.decttype(self.startaddr[i])
            endaddrtype = self.decttype(self.endaddr[i])

            if startaddrtype != endaddrtype:
                raise TypeError('startaddr: %s and endaddr: %s are different type in one range' %(self.startaddr[i], self.endaddr[i]))

            elif startaddrtype == 'ipv4' or startaddrtype == 'ipv6':
                startaddr = IPNetwork(self.startaddr[i])
                endaddr = IPNetwork(self.endaddr[i])
                if startaddr.network != endaddr.network:
                    raise ValueError('startaddr: %s and endaddr: %s are not in same subnet in one range' %(self.startaddr[i], self.endaddr[i]))
                elif startaddr.ip > endaddr.ip:
                    raise ValueError('startaddr：%s is bigger than endaddr: %s in one range' %(self.startaddr[i], self.endaddr[i]))
                elif startaddr.ip == endaddr.ip:
                    ans += self.startaddr[i] + ','
                elif startaddr.ip < endaddr.ip:
                    ans += self.startaddr[i] + '-' + self.endaddr[i] + ','

            elif startaddrtype == 'macaddr':
                startaddrval = self.addr2int(self.startaddr[i])
                endaddrval = self.addr2int(self.endaddr[i])
                if startaddrval > endaddrval:
                    raise ValueError('startaddr: %s is bigger than endaddr: %s in one range' %(self.startaddr[i], self.endaddr[i]))
                elif startaddrval == endaddrval:
                    ans += self.startaddr[i] + ','
                elif startaddrval < endaddrval:
                    ans += self.startaddr[i] + '-' + self.endaddr[i] + ','
            elif self.startaddr[i].replace(' ', '') == '':
                continue
            elif startaddrtype == 'string':
                if self.startaddr[i] != self.endaddr[i]:
                    raise ValueError('startaddr: %s and endaddr: %s are not same string' %(self.startaddr[i], self.endaddr[i]))
                else:
                    ans += self.startaddr[i] + ','
        return ans[:-1]




    def getRandom(self): # assuming that we dont delete the getaddr
        index = random.randint(0, len(self.startaddr) - 1)
        startaddrtype = self.decttype(self.startaddr[index])
        endaddrtype = self.decttype(self.endaddr[index])
        if self.startaddr[index] == self.endaddr[index]:# string or single addr
            getaddr = self.startaddr[index]
        else:# not string
            startaddrval = self.addr2int(self.startaddr[index])
            endaddrval = self.addr2int(self.endaddr[index])
            movval = random.randint(0, endaddrval - startaddrval - 1)
            print('movval=', movval)
            getaddr = self.movaddr(self.startaddr[index], movval)
        return getaddr





