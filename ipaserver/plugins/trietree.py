#!/usr/bin/env python
# _*_ coding:utf-8 _*_
"""
Your Trie object will be instantiated and called as such:
trie = Trie()
trie.insert("lintcode")
trie.search("lint") will return false
trie.startsWith("lint") will return true


a = '192.168.1.1'
b = a[:-1]
b
'192.168.1.'
a[-1]
'1'
a[-2]
'.'
a = 'abcdefghijklnm!23'
a[:-1]
'abcdefghijklnm!2'
a[-1]
'3'
"""
from netaddr import *
import random
import re

DEFAULT_IP_RANGE = '192.168.0.2-192.168.0.254'
IPV4_Interval = 256

class TrieNode:
    def __init__(self):
        # Initialize data structure. Each Node has 256 childNode
        self.childs = dict()
        self.isIP = False



class Trie:
    def __init__(self):
        self.root = TrieNode()

        # @param {string} IP
        # @return {void}
        # Inserts a IP into the trie.

    def insert(self, IP): #insert single one node
        node = self.root
        # parts = IP.replace(" ","").split(".")
        IP = IP.replace(' ', '')
        parts = re.split('\:|\.',IP)
        for part in parts:
            child = node.childs.get(part) # part可能不存在,用x.get(part)而不用x[part]
            if child is None:
                child = TrieNode()
                node.childs[part] = child
            node = child
        node.isIP = True

        # @param {string} IP
        # @return {boolean}
        # Returns if the IP is in the trie.

    def search(self, IP):
        node = self.root
        IP = IP.replace(' ', '')
        parts = re.split('\:|\.', IP)

        for part in parts:
            if re.match(
                    r'^(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])((\.(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])){3})$',
                    IP):
                part = ('00'+ part)[-3:]
            elif re.match(
                    r'^\s*((([0-9A-Fa-f]{1,4}:){7}(([0-9A-Fa-f]{1,4})|:))|(([0-9A-Fa-f]{1,4}:){6}(:|((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})|(:[0-9A-Fa-f]{1,4})))|(([0-9A-Fa-f]{1,4}:){5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){4}(:[0-9A-Fa-f]{1,4}){0,1}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){3}(:[0-9A-Fa-f]{1,4}){0,2}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){2}(:[0-9A-Fa-f]{1,4}){0,3}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:)(:[0-9A-Fa-f]{1,4}){0,4}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(:(:[0-9A-Fa-f]{1,4}){0,5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})))(%.+)?\s*$',
                    IP):
                part = ('000' + part)[-4:]

            node = node.childs.get(part)
            if node is None:
                return False
        return node.isIP

    def delete(self, IP): #not yet support ipv6
        node = self.root
        IP = IP.replace(' ', '')
        parts = re.split('\:|\.', IP)

        for part in parts:
            if re.match(
                    r'^(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])((\.(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])){3})$',
                    IP):
                part = ('00'+ part)[-3:]
            elif re.match(
                    r'^\s*((([0-9A-Fa-f]{1,4}:){7}(([0-9A-Fa-f]{1,4})|:))|(([0-9A-Fa-f]{1,4}:){6}(:|((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})|(:[0-9A-Fa-f]{1,4})))|(([0-9A-Fa-f]{1,4}:){5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){4}(:[0-9A-Fa-f]{1,4}){0,1}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){3}(:[0-9A-Fa-f]{1,4}){0,2}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){2}(:[0-9A-Fa-f]{1,4}){0,3}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:)(:[0-9A-Fa-f]{1,4}){0,4}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(:(:[0-9A-Fa-f]{1,4}){0,5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})))(%.+)?\s*$',
                    IP):
                part = ('000' + part)[-4:]

            node = node.childs.get(part)
            if node is None:
                return
        node.isIP = False


        # @param {string} prefix
        # @return {boolean}
        # Returns if there is any IP in the trie
        # that starts with the given prefix.

    def startsWith(self, prefix):
        node = self.root
        IP = IP.replace(' ', '')
        parts = re.split('\:|\.', IP)

        
        for part in parts:
            node = node.childs.get(part)
            if node is None:
                return False
        return True

    def poolSet(self, iprange):#input from LDAP #support ipv6
        if iprange is None:
            return
        iprange = iprange.replace(' ', '')
        if iprange == '':
            return
        if iprange.lower() == 'any':
            iprange = DEFAULT_IP_RANGE
        iprangeList = iprange.split(",")
        for oneiprange in iprangeList:
            if oneiprange == '':
                continue
            iprangeEnds = oneiprange.split("-")
            if len(iprangeEnds) == 1:

                start = iprangeEnds[0]
                if re.match(r'^(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])((\.(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])){3})$', start):
                    starttmp = ''
                    for st in start.split('.'): # convert '192.169.001.097'into '192.169.1.97'
                        starttmp += str(int(st)) + '.'

                    start = IPAddress(starttmp[:-1]).value

                    ip = str(IPAddress(start)) #convert '192.168.1.10' into '192.168.001.010' for Bestring function
                    ip = ('00'+ip.split(".")[0])[-3:] + "." + ('00'+ip.split(".")[1])[-3:] + "." + ('00'+ip.split(".")[2])[-3:] + "." + ('00'+ip.split(".")[3])[-3:]
                    self.insert(ip)

                elif re.match(r'^\s*((([0-9A-Fa-f]{1,4}:){7}(([0-9A-Fa-f]{1,4})|:))|(([0-9A-Fa-f]{1,4}:){6}(:|((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})|(:[0-9A-Fa-f]{1,4})))|(([0-9A-Fa-f]{1,4}:){5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){4}(:[0-9A-Fa-f]{1,4}){0,1}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){3}(:[0-9A-Fa-f]{1,4}){0,2}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){2}(:[0-9A-Fa-f]{1,4}){0,3}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:)(:[0-9A-Fa-f]{1,4}){0,4}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(:(:[0-9A-Fa-f]{1,4}){0,5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})))(%.+)?\s*$', start):
                    starttmp = ''
                    for st in start.split(':'): # convert 'ffff:ffff:ffff:ffff:0001:0001:0001:0001'into '....:1:1:1:1'
                        starttmp += "{:01x}".format(int(st,16))[-4:]+':'

                    start = IPAddress(starttmp[:-1]).value


                    ip = str(IPAddress(start)) #convert '192.168.1.10' into '192.168.001.010' for Bestring function
                    iptmp = ''
                    for seg in ip.split(':'):
                        iptmp += "{:012x}".format(int(seg,16))[-4:]+':'
                        self.insert(iptmp[:-1])

                elif re.match(r'^([a-fA-F0-9]{2}[:|\-]?){5}[a-fA-F0-9]{2}$', start):
                    #convert string to int (macaddr to number)
                    macstart = int(start.encode('utf-8').translate(None ,b":.- "), 16) #string has to be converted into python2 byte type


                    mac_hex = "{:012x}".format(start)
                    mac_str = ":".join(mac_hex[i:i + 2] for i in range(0, len(mac_hex), 2))#convert mac_int into mac_str
                    ip = str(mac_str)
                    self.insert(ip)

                else:
                    #pass #throw exception
                    strstart = start
                    self.insert(strstart)


            elif len(iprangeEnds) == 2 and iprangeEnds[0] == '':

                start = iprangeEnds[1]
                if re.match(r'^(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])((\.(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])){3})$',
                            start):
                    starttmp = ''
                    for st in start.split('.'):  # convert '192.169.001.097'into '192.169.1.97'
                        starttmp += str(int(st)) + '.'

                    start = IPAddress(starttmp[:-1]).value

                    ip = str(IPAddress(start))  # convert '192.168.1.10' into '192.168.001.010' for Bestring function
                    ip = ('00' + ip.split(".")[0])[-3:] + "." + ('00' + ip.split(".")[1])[-3:] + "." + ('00' +
                                                                                                        ip.split(".")[
                                                                                                            2])[
                                                                                                       -3:] + "." + (
                                                                                                                    '00' +
                                                                                                                    ip.split(
                                                                                                                        ".")[
                                                                                                                        3])[
                                                                                                                    -3:]
                    self.insert(ip)

                elif re.match(
                        r'^\s*((([0-9A-Fa-f]{1,4}:){7}(([0-9A-Fa-f]{1,4})|:))|(([0-9A-Fa-f]{1,4}:){6}(:|((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})|(:[0-9A-Fa-f]{1,4})))|(([0-9A-Fa-f]{1,4}:){5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){4}(:[0-9A-Fa-f]{1,4}){0,1}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){3}(:[0-9A-Fa-f]{1,4}){0,2}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){2}(:[0-9A-Fa-f]{1,4}){0,3}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:)(:[0-9A-Fa-f]{1,4}){0,4}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(:(:[0-9A-Fa-f]{1,4}){0,5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})))(%.+)?\s*$',
                        start):
                    starttmp = ''
                    for st in start.split(':'):  # convert 'ffff:ffff:ffff:ffff:0001:0001:0001:0001'into '....:1:1:1:1'
                        starttmp += "{:01x}".format(int(st, 16))[-4:] + ':'

                    start = IPAddress(starttmp[:-1]).value

                    ip = str(IPAddress(start))  # convert '192.168.1.10' into '192.168.001.010' for Bestring function
                    iptmp = ''
                    for seg in ip.split(':'):
                        iptmp += "{:012x}".format(int(seg, 16))[-4:] + ':'
                        self.insert(iptmp[:-1])

                elif re.match(r'^([a-fA-F0-9]{2}[:|\-]?){5}[a-fA-F0-9]{2}$', start):
                    # convert string to int (macaddr to number)
                    macstart = int(start.encode('utf-8').translate(None, b":.- "),
                                   16)  # string has to be converted into python2 byte type

                    mac_hex = "{:012x}".format(start)
                    mac_str = ":".join(
                        mac_hex[i:i + 2] for i in range(0, len(mac_hex), 2))  # convert mac_int into mac_str
                    ip = str(mac_str)
                    self.insert(ip)

                else:
                    # pass #throw exception
                    strstart = start
                    self.insert(strstart)
            elif len(iprangeEnds) == 2:
                start = iprangeEnds[0]
                end = iprangeEnds[1]
                # use regular expression to decide which type of this address
                if re.match(r'^(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])((\.(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])){3})$', start):
                    starttmp = ''
                    for st in start.split('.'): # convert '192.169.001.097'into '192.169.1.97'
                        starttmp += str(int(st)) + '.'

                    endtmp = ''
                    for ed in end.split('.'):
                        endtmp += str(int(ed)) + '.'

                    start = IPAddress(starttmp[:-1]).value
                    end = IPAddress(endtmp[:-1]).value
                    for part in range(start, end + 1):
                        ip = str(IPAddress(part)) #convert '192.168.1.10' into '192.168.001.010' for Bestring function
                        ip = ('00'+ip.split(".")[0])[-3:] + "." + ('00'+ip.split(".")[1])[-3:] + "." + ('00'+ip.split(".")[2])[-3:] + "." + ('00'+ip.split(".")[3])[-3:]
                        self.insert(ip)
                elif re.match(r'^\s*((([0-9A-Fa-f]{1,4}:){7}(([0-9A-Fa-f]{1,4})|:))|(([0-9A-Fa-f]{1,4}:){6}(:|((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})|(:[0-9A-Fa-f]{1,4})))|(([0-9A-Fa-f]{1,4}:){5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){4}(:[0-9A-Fa-f]{1,4}){0,1}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){3}(:[0-9A-Fa-f]{1,4}){0,2}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:){2}(:[0-9A-Fa-f]{1,4}){0,3}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(([0-9A-Fa-f]{1,4}:)(:[0-9A-Fa-f]{1,4}){0,4}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(:(:[0-9A-Fa-f]{1,4}){0,5}((:((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})?)|((:[0-9A-Fa-f]{1,4}){1,2})))|(((25[0-5]|2[0-4]\d|[01]?\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]?\d{1,2})){3})))(%.+)?\s*$', start):
                    starttmp = ''
                    for st in start.split(':'): # convert 'ffff:ffff:ffff:ffff:0001:0001:0001:0001'into '....:1:1:1:1'
                        starttmp += "{:01x}".format(int(st,16))[-4:]+':'

                    endtmp = ''
                    for ed in end.split(':'):
                        endtmp += "{:01x}".format(int(ed,16))[-4:]+':'

                    start = IPAddress(starttmp[:-1]).value
                    end = IPAddress(endtmp[:-1]).value
                    for part in range(start, end + 1):
                        ip = str(IPAddress(part)) #convert '192.168.1.10' into '192.168.001.010' for Bestring function
                        iptmp = ''
                        for seg in ip.split(':'):
                            iptmp += "{:012x}".format(int(seg,16))[-4:]+':'
                        self.insert(iptmp[:-1])
                elif re.match(r'^([a-fA-F0-9]{2}[:|\-]?){5}[a-fA-F0-9]{2}$', start):
                    #convert string to int (macaddr to number)
                    macstart = int(start.encode('utf-8').translate(None ,b":.- "), 16) #string has to be converted into python2 byte type
                    macend = int(end.encode('utf-8').translate(None ,b":.- "), 16)
                    for part in range(macstart, macend + 1):
                        mac_hex = "{:012x}".format(part)
                        mac_str = ":".join(mac_hex[i:i + 2] for i in range(0, len(mac_hex), 2))#convert mac_int into mac_str
                        ip = str(mac_str)
                        self.insert(ip)
                else:
                    #pass #throw exception
                    strstart = start
                    strend = end
                    self.insert(strstart)
                    self.insert(strend)
        return

    def stringtoascii(self, str):
        if re.match(r'^(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])((\.(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])){3})$', str):
            sum = 0
            ten = 1
            for i in range(len(str), 0, -1):
                sum += ord(str[i - 1]) * ten  # <<2*i
                ten = ten * 10

        else :
            sum = int(str.encode('utf-8').translate(None, b":.- "), 16)

        return sum

    def beString(self, type): # Output from LDAP
        def dfs(node, result, tmp):  # tmp = ''
            if node.isIP == True:
                result += [tmp[:-1]]

            else:
                for part in sorted(node.childs.keys()):
                    if node.childs.get(part) != None:
                        dfs(node.childs.get(part), result, tmp + (str(int(part)) + '.' if type == 'ipv4' else str(part) + ':'))
                        #dfs(node.childs[choice(node.childs.keys())], result, tmp + str(part) + '.')

        node = self.root
        result = []
        tmp = ''
        dfs(node, result, tmp)
        startip = ''
        tempip = ''
        endip = ''
        ans =''
        print(result)
        for addr in result:
            addr_int = self.stringtoascii(addr)
            if len(result) == 1 :
                return result[0]

            if startip == '':
                startip = addr
                tempip = addr
            elif self.stringtoascii(tempip) + 1 == addr_int and addr != result[-1]:
                tempip = addr
            elif self.stringtoascii(tempip) + 1 == addr_int and addr == result[-1]:
                endip = addr
                ans += startip + '-' + endip + ','
            elif self.stringtoascii(tempip) + 1 != addr_int and addr == result[-1]:
                endip = tempip
                if startip == endip:
                    ans += startip + ','+ addr +','
                else:
                    ans += startip + '-' + endip + ','+ addr +','
            else:
                endip = tempip
                if startip == endip:
                    ans += startip + ','
                else:
                    ans += startip + '-' + endip + ','
                startip = addr
                tempip = addr
        return ans[:-1]

    def getRandom(self, type):
        #way1: split dfs and beString      pick random index of result then delete this node return this node then output this IPpool
        #way2: traverse the first node or first randomly node
        def dfs2(node, tmp):  # tmp = ''
            if node.isIP == True:
                return tmp[:-1]

            else:
                for part in node.childs.keys():
                    if node.childs.get(part) != None:
                        return dfs2(node.childs.get(part), tmp + (str(int(part)) + '.' if type == 'ipv4' else str(part) + ':'))


         #递归中需要return数值的时候，在调用递归的时候也许要用return，否则返回为None

        node = self.root
        tmp = ''
        ans = dfs2(node, tmp)
        self.delete(ans)
        return ans



