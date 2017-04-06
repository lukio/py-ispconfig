"""
# ###############################################################################
#
# PyISPconfig - Benjamin Bouvier (benjamin.bouvier29@gmail.com)
#
################################################################################
# Copyright (c) 2012, Bouvier
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# Neither the name of Benjamin Bouvier. nor the names of its contributors may
# be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
################################################################################
"""
import random
from SOAPpy import SOAPProxy
from SOAPpy import Types
from SOAPpy import *


class PyISPconfig(object):
    """ A simple wrapper around the ISPconfig API """

    def __init__(self, ip, login, password, port=8080):
        """
        The constructor.

        Param:
        ip -- The server's IP.
        login -- remote user's Login.
        password -- remote user's Password.
        port -- The port of IspConfig on remote server (default 8080).

        """
        self.ip = ip
        self.login = login
        self.password = password
        self.port = port
        self.session_id = None
        self.error = {}

        #Creates the base url
        self.url = "https://%s:%s/remote/" % (self.ip, self.port)
        #Soap connexion to remote server
        self.server = SOAPProxy(self.url)
        #Setting off debug mode
        self.server.config.dumpSOAPOut = 0
        self.server.config.dumpSOAPIn = 0
        #Login as remote user
        if not self.session_id:
            self.session_id = self._call("login", (self.login, self.password))

    def _call(self, method, params=None):
        """
        Do an soap request to the ISPconfig API and return the result.
        """

        if self.session_id:
            #Add the session_id a the beginning of params
            session_id = (self.session_id,)
            if params:
                if isinstance(params, int):
                    params = session_id + (params,)
                elif isinstance(params, dict):
                    params = session_id + (params,)
                elif isinstance(params, list):
                    params = session_id + (params,)
                elif isinstance(params, tuple):
                    params = session_id + params
                else:
                    params = session_id + (params,)
        try:
            #Invoke asked method on the server
            response = self.server.invoke(method, args=params)
        except faultType as e:
            self.error = {"error": True, "type": "faultType", "detail": e.faultstring}
            return False
        else:
            if not response:
                self.error = {"error": True, "type": "string", "detail": "SOAP request return null"}
            return response

    def check_response(self, response, type, error_message="Problem during check response"):
        """
        Checking type of a response and return error message.

        Param:
            params -- The array

        """
        if isinstance(response, type):
            return response
        else:
            if isinstance(response, dict) and response.get('error'):
                if response['error']:
                    self.error = {"error": True, "type": response['type'], "detail": response['detail']}
                    return False
            else:
                self.error = {"error": True, "type": "string", "detail": error_message}
                return False

    def array_to_dict_response(self, params):
        """
        Convert the array element recieved by SOAP in a Dictionary .

        Param:
            params -- The array

        """
        dictionary = {}
        rs = simplify(params)

        if isinstance(rs, list):
            for test in rs:
                dictionary[test['item']['key']] = test['item']['value']
            return dictionary
        elif isinstance(rs, dict):
            for test in rs['item']:
                dictionary[test['key']] = test['value']
            return dictionary
        else:
            return False

    def update_default_dict(self, default, params=None):
        """
        Update default dict params if needed

        Param:
            default -- The default Dictionary .
            params -- The Dictionary  containing parameters to update.
        """
        if params:
            default.update(params)
        return default

    """
    def update_tuple_list(self,params_by_default, params = None):

        Update default params tuple if needed

        Param:
        params_by_default -- The default list of tuple.
        params -- The list of tuple containing the parameters to update.

        if params:
            for x, y in params:
                i = 0
                for x_default, y_default in params_by_default:
                    if x_default == x:
                        params_by_default[i] = (x_default,y)
                    i +=1
        return params_by_default
    """

    def dict_to_tuple(self, dict):
        """
        Convert Dictionary  to tuple for ISP config API

        Param:
        dict -- The Dictionary  parameters.
        """
        list = []
        for k, v in dict.iteritems():
            list.append((k, v))
        return list

    def tuple_to_array(self, list_of_tuples):
        from collections import OrderedDict
        my_dict = OrderedDict(list_of_tuples)
        for key, value in my_dict.iteritems():
            print '%s = %s' % (key, value)

#
# Actions on Client
#

    def client_get(self, id):
        """
        Retrieves information about a client.

        Param:
            id -- Client id.

        Output:
            Return a Dictionary with key/values of the chosen client.
        """
        response = self.array_to_dict_response(self._call("client_get", id))
        if response:
            return self.check_response(response, dict, "Error during 'client_get' method")
        else:
            self.error = {"error": True, "type": "string", "detail": "Client ID %s doesn't exist" % id}
            return self.error

    def client_add(self, params=None, reseller_id=0):
        """
        Add a new client

        Param:
            reseller_id -- Reseller's ID.
            param -- Dictionary  containing client's informations.

        Output:
            Returns the ID of the newly added Client.

        """
        reseller_id = 0
        default = {"company_name": "awesomecompany",
                    "contact_name": "mynamecopntact",
                    "customer_no": "1",
                    "vat_id": "1",
                    "street": "fleetstreet",
                    "zip": "21337",
                    "city": "london",
                    "state": "bavaria",
                    "country": "UK",
                    "telephone": "123456789",
                    "mobile": "987654321",
                    "fax": "546718293",
                    "email": "e@mail.int",
                    "internet": "",
                    "icq": "111111111",
                    "notes": "awesome",
                    "dafault_mailserver": 1,
                    "limit_maildomain": -1,
                    "limit_mailbox": -1,
                    "limit_mailalias": -1,
                    "limit_mailaliasdomain": -1,
                    "limit_mailforward": -1,
                    "limit_mailcatchall": -1,
                    "limit_mailrouting": 0,
                    "limit_mailfilter": -1,
                    "limit_fetchmail": -1,
                    "limit_mailquota": -1,
                    "limit_spamfilter_wblist": 0,
                    "limit_spamfilter_user": 0,
                    "limit_spamfilter_policy": 1,
                    "default_webserver": 1,
                    "limit_web_ip": "",
                    "limit_web_domain": -1,
                    "limit_web_quota": -1,
                    "web_php_options": "no",
                    "limit_web_subdomain": -1,
                    "limit_web_aliasdomain": -1,
                    "limit_ftp_user": -1,
                    "limit_shell_user": 0,
                    "ssh_chroot": "no",
                    "limit_webdav_user": 0,
                    "default_dnsserver": 1,
                    "limit_dns_zone": -1,
                    "limit_dns_slave_zone": -1,
                    "limit_dns_record": -1,
                    "default_dbserver": 1,
                    "limit_database": -1,
                    "limit_cron": 0,
                    "limit_cron_type": "url",
                    "limit_cron_frequency": 5,
                    "limit_traffic_quota": -1,
                    "limit_client": 0,
                    "parent_client_id": 0,
                    "username": "user2",
                    "password": "brush",
                    "language": "en",
                    "usertheme": "default",
                    "template_master": 0,
                    "template_additional": "",
                    "created_at": 0}

        params = self.dict_to_tuple(self.update_default_dict(default, params))

        #Execute method
        return self.check_response(self._call("client_add", (reseller_id, params)), int, "Error during 'client_add' method")

    def client_get_id(self, id):
        """
        Retrieves the client ID of the system user

        Param:
            username -- System user ID

        Output:
            Returns the client ID of the user with the entered system user ID.
        """
        response = self._call("client_get_id", id)
        if response:
            return response
        else:
            self.error = {"error": True, "type": "string", "detail": "client ID of the system user %s doesn't exist" % id}
            return False


    def client_get_by_username(self, username):
        """
        Return the client's information by username

        Param:
            username -- Client's username

        Output:
            Return a Dictionary with key/values of the chosen client.
        """

        response = self.array_to_dict_response(self._call("client_get_by_username", username))
        if response:
            return self.check_response(response, dict, "Error during 'client_get_by_username' method")
        else:
            self.error = {"error": True, "type": "string", "detail": "Client username %s doesn't exist" % username}
            return self.error

    def client_change_password(self, id, password):
        """
        Return the client's information

        Param:
            username -- Client's username

        Output:
            Returns '1' if password has been changed.
        """

        response = self._call("client_change_password", (id, password))
        if response:
            return self.check_response(response, int, "Error during 'client_change_password' method")
        else:
            self.error = {"error": True, "type": "string", "detail": "Problem during password's modification"}
            return False
#
# Actions on Databases
#
    def sites_database_add(self, client_id, params=None):
        """
        Adds a new database.

        Param:
            id -- Client's id
            param -- Dictionary containing client's informations.

        Output:
            Returns the ID of the newly added database.
        """
        db_name_exist = db_username_exist = False
        existing_db_name = existing_username = False
        rand = random.randint(1, 10000)
        new_db_params = None
        default = {"server_id": 1,
                   "type": "mysql",
                   "database_name": "db_user%s%s" % (client_id, rand),
                   "database_user": "db_user%s%s" % (client_id, rand),
                   "database_password": "db_user",
                   "database_charset": "UTF8",
                   "remote_access": "y",
                   "remote_ips": "",
                   "active": "y"}
        user_db = self.sites_database_get_all_by_user(client_id)

        #Update default params
        default = self.update_default_dict(default, params)

        # Check database name and username doesn't exist
        for db in user_db:
            if db['database_name'] == default["database_name"]:
                db_name_exist = True
                existing_db_name = db['database_name']
            if db['database_user'] == default["database_user"]:
                db_username_exist = True
                existing_username = db['database_user']


        # Check new database's name doesn't exist and changes it
        if db_name_exist or db_username_exist:
            while db_name_exist or db_username_exist:
                #Create new params
                db_name_exist = db_username_exist = False
                rand = random.randint(1, 10000)
                new_db_params = {"database_name": "%s%s" % (existing_db_name, rand),
                                "database_user": "%s%s" % (existing_username, rand), }
                #Recheck params doesn't exist in db
                for db in user_db:
                    if db['database_name'] == new_db_params["database_name"]:
                        db_name_exist = True
                        existing_db_name = db['database_name']
                    if db['database_user'] == new_db_params["database_user"]:
                        db_username_exist = True
                        existing_username = db['database_user']
                #Update params by new params
                default = self.update_default_dict(default, new_db_params)
        #SOAPRequest
        default = self.dict_to_tuple(default)

        response = self._call("sites_database_add", (client_id, default))
        #Check response
        return self.check_response(response, int, "Error during 'sites_database_add' method")

    def sites_database_get(self, id):
        """
        Retrieves information about a database.

        Param:
            id -- Databse's id

        Output:
            Return a Dictionary with key/values of the chosen database.
        """
        response = self.array_to_dict_response(self._call("sites_database_get", id))
        if response:
            return self.check_response(response, dict, "Error during 'sites_database_get' method")
        else:
            self.error = {"error": True, "type": "string", "detail": "Database ID %s doesn't exist" % id}
            return False

    def sites_database_delete(self, id):
        """
        Deletes a database.

        Param:
            id -- Databse's id

        Output:
            Returns the number of deleted records.
        """

        response = self._call("sites_database_delete", id)
        if response:
            return self.check_response(response, int, "Error during 'sites_database_delete' method")
        else:
            self.error = {"error": True, "type": "string", "detail": "Problem during deleting Database ID %s" % id}
            return False

    def sites_database_get_all_by_user(self, client_id):
        """
        Returns information about the databases of the system user.

        Param:
            client_id -- Client's id

        Output:
            Return a list of Dictionaries with key/values with databases's values.
        """

        response = self._call("sites_database_get_all_by_user", client_id)
        if not response:
            self.error = {"error": True, "type": "string", "detail": "No database for client ID %s" % client_id}
            return False
        else:
            list = []
            if isinstance(response, typedArrayType):
                for answer in response:
                    list.append(self.array_to_dict_response(answer))
            #Check response
            return self.check_response(list, type(list), "Error during 'sites_database_get_all_by_user' method")

    def sites_database_update(self, db_id, params=None):
        """
        Updates a database.

        Param:
            client_id -- Client's id
            db_id -- Databse's id
            params -- Dictionary  containing database's informations to update.

        Output:
            Returns the number of affected rows.
        """
        new_params = None
        dict_example = {'server_id': '1',
                        'sys_perm_other': '',
                        'sys_perm_user': 'riud',
                        'sys_userid': '1',
                        'sys_groupid': '9',
                        'remote_access': 'y',
                        'active': 'y',
                        'database_id': '3',
                        'database_charset': 'utf8',
                        'sys_perm_group': 'ru',
                        'database_password': '*E7FFA47F56E1835B4A9EB44301E23746C127E263',
                        'remote_ips': '',
                        'type': 'mysql',
                        'database_name': 'c8c8db_name2',
                        'database_user': 'c8c8db_name2'}

        #Get original database configuration
        origin = self.sites_database_get(db_id)
        if not origin:
            return {"error": True, "type": "string", "detail": "Database doesn't exist"}
        else:
            #Update original database configuration
            new_params = self.dict_to_tuple(self.update_default_dict(origin, params))
            #SOAPRequest
            response = self._call("sites_database_update", (origin['sys_groupid'], db_id, new_params))
            #Check response
            return self.check_response(response, int, "Error during 'sites_database_update' method")

#
# Actions on Server
#
    def server_get(self, server_id):
        """
        Returns server information by its ID.

        Param:
        server_id -- Server's id

        Output:
            Return a Dictionary with key/values with the server parameter's values.
        """

        #SOAPRequest
        response = self._call("server_get", server_id)
        if response:
            response = self.array_to_dict_response(response)
            return self.check_response(response, dict, "Error during 'server_get' method")
        else:
            return {"error": True, "type": "string", "detail": "Server doesn't exist"}

    #
    # TODO
    # Problem with self._call("server_get_serverid_by_ip",ipaddress)
    # return an empty arraytype

    def server_get_serverid_by_ip(self, ipaddress):
        """
        Returns server information by its IP.

        Param:
        ipaddress -- Server's ip

        Output:
            Return a Dictionary with key/values with the server parameter's values.
        """

        response = self.array_to_dict_response(self._call("server_get_serverid_by_ip", ipaddress))
        if response:
            return self.check_response(response, dict, "Error during 'server_get_serverid_by_ip' method")
        else:
            return {"error": True, "type": "string", "detail": "Server doesn't exist with %s IP Adress" % ipaddress}


    def logout(self):
        """
        Cancels a remote session.

        Output:
            None.
        """
        self._call("logout")
        return True

    def error_message(self):
        """
        Display readable error message.

        Output:
            Return string error message.
        """
        if(self.error.get('error') and self.error['error']):
            return str(self.error['detail'])
        else:
            return "No error message"

#
# Actions on DNS
#
    def dns_zone_get_id(self, domain):
        """
        Return the dns zone id by domain name

        Param:
            domain -- Client's username

        Output:
            Returns the ID of the find dns zone by id.
        """

        response = self._call("dns_zone_get_id", domain)
        if response:
            return response
        else:
            self.error = {"error": True, "type": "string", "detail": "DNS zone %s doesn't exist" % domain}
            return False

    def dns_zone_get(self, zone_id):
        """
        Returns dns zone information by its id.

        Param:
        zone_id - ID of DNS zone

        Output:
            Return a Dictionary with key/values with the zone parameter's values.
        """

        response = self.array_to_dict_response(self._call("dns_zone_get", zone_id))
        if response:
            return self.check_response(response, dict, "Error during 'dns_zone_get' method")
        else:
            return {"error": True, "type": "string", "detail": "Zone doesn't exist with ID %s" % zone_id}

    def dns_a_get_id(self, dns_zone_id, record):
        """
        Return the record id by name and zone ID

        Param:
            dns_zone_id - zone ID
            record - name of record in zone dns_zone_id

        Output:
            Returns the ID of the find record in zone.
        """

        response = self._call("dns_a_get_id", (dns_zone_id,record))
        if response:
            return response
        else:
            self.error = {"error": True, "type": "string", "detail": "DNS record %s doesn't exist" % record}
            return False

    def dns_a_add(self, client_id, params=None):
        """
        Adds a new DNS A record.

        Param:
            id -- Client's id
            param -- Dictionary containing record's informations.

        Output:
            Returns the ID of the newly added record.
        """

        default = {"server_id": 1,
                   "zone": 1,
                   "name": "www",
                   "data": "127.0.0.1",
                   "ttl": "3600",
                   "type": "A",
                   "active": "y"}

        # Search server id by zone
        if params['zone']:
            server_id = self.dns_zone_get(params['zone'])
            if server_id:
                params['server_id'] = server_id['server_id']

        #Update default params
        default = self.update_default_dict(default, params)

        #SOAPRequest
        default = self.dict_to_tuple(default)

        response = self._call("dns_a_add", (client_id, default))
        #Check response
        return self.check_response(response, int, "Error during 'dns_a_add' method")

    def dns_a_delete(self, id):
        """
        Deletes A record.

        Param:
        id - ID of DNS zone to delete

        Output:
            Returns the number of deleted records.
        """

        response = self._call("dns_a_delete", id)

        if response:
            return self.check_response(response, int, "Error during 'dns_a_delete' method")
        else:
            self.error = {"error": True, "type": "string", "detail": "Problem during deleting A record ID %s" % id}
            return False

    def dns_mx_get_id(self, dns_zone_id, record):
        """
        Return the record id by name and zone ID

        Param:
            dns_zone_id - zone ID
            record - name of record in zone dns_zone_id

        Output:
            Returns the ID of the find record in zone.
        """

        response = self._call("dns_mx_get_id", (dns_zone_id,record))
        if response:
            return response
        else:
            self.error = {"error": True, "type": "string", "detail": "DNS record %s doesn't exist" % record}
            return False

    def dns_mx_add(self, client_id, params=None):
        """
        Adds a new DNS MX record.

        Param:
            id -- Client's id
            param -- Dictionary containing record's informations.

        Output:
            Returns the ID of the newly added record.
        """

        default = {"server_id": 1,
                   "zone": 1,
                   "name": "www",
                   "data": "127.0.0.1",
                   "aux": 10,
                   "ttl": "3600",
                   "type": "MX",
                   "active": "y"}

        # Search server id by zone
        if params['zone']:
            server_id = self.dns_zone_get(params['zone'])
            if server_id:
                params['server_id'] = server_id['server_id']

        #Update default params
        default = self.update_default_dict(default, params)

        #SOAPRequest
        default = self.dict_to_tuple(default)

        response = self._call("dns_mx_add", (client_id, default))
        #Check response
        return self.check_response(response, int, "Error during 'dns_mx_add' method")

    def dns_mx_delete(self, id):
        """
        Deletes A record.

        Param:
        id - ID of DNS zone to delete

        Output:
            Returns the number of deleted records.
        """

        response = self._call("dns_mx_delete", id)

        if response:
            return self.check_response(response, int, "Error during 'dns_mx_delete' method")
        else:
            self.error = {"error": True, "type": "string", "detail": "Problem during deleting A record ID %s" % id}
            return False

    def domains_get_all_by_user(self, group_id):
        """
        Returns information about the databases of the system user.

        Param:
            client_id -- Client's id
            group_id -- Group's id

        Output:
            Return a list of Dictionaries with key/values with domain's values.
        """

        #response = self._call("domains_get_all_by_user", (client_id, group_id))
        response = self.array_to_dict_response(self._call("domains_get_all_by_user", group_id))
        if not response:
            self.error = {"error": True, "type": "string", "detail": "No domain for client ID %s" % client_id}
            return self.error
        else:
            list = []
            if isinstance(response, typedArrayType):
                for answer in response:
                    list.append(self.array_to_dict_response(answer))
            #Check response
            return self.check_response(list, type(list), "Error during 'domains_get_all_by_user' method")

    def client_get_groupid(self, client_id):
        """
        Return the group id by client

        Param:
            client_id - Client's ID

        Output:
            Returns the ID of the group
        """

        response = self._call("client_get_groupid", client_id)
        if response:
            return response
        else:
            self.error = {"error": True, "type": "string", "detail": "There is no group for this client ID: %s" % client_id}
            return False

    def mail_domain_get(self, params=None):
        """
        Returns mail domain information by its group id.

        Param:
            param -- Dictionary containing mail domain information.

        Output:
            Return a Dictionary with key/values with the mail domain parameter's values.
        """
        response = self._call("mail_domain_get", params)
        if response:
            return response
        else:
            return {"error": True, "type": "string", "detail": "Mail domain doesn't exist."}

    def mail_user_get(self, params=None):
        """
        Returns mail user information by its group id.

        Param:
            param -- Dictionary containing mail user information.

        Output:
            Return a Dictionary with key/values with the mail mail parameter's values.
        """

        response = self._call("mail_user_get", params)
        if response:
            return response
        else:
            return {"error": True, "type": "string", "detail": "Mail user doesn't exist."}

    def mail_user_set(self, client_id, mailuser_id, params=None):
        """
        Returns mail user information by its group id.

        Param:
            param -- Dictionary containing mail user information.

        Output:
            Return a Dictionary with key/values with the mail mail parameter's values.
        """
        default = {
            'disableimap': 'n',
            'disablepop3': 'n',
            'disabledeliver': 'n',
            'disablesmtp': 'n',
        }

        ##Update default params
        #import ipdb; ipdb.set_trace()  # XXX BREAKPOINT
        params = {}
        params['disableimap'] = 'y'
        default = self.update_default_dict(default, params)

        ##SOAPRequest
        default = self.dict_to_tuple(default)

        response = self._call("mail_user_update_pythonic", (client_id, mailuser_id, default))
        return response
        #if response:
        #    return response
        #else:
        #    return {"error": True, "type": "string", "detail": "Mail user doesn't exist."}

    def sites_web_domain_get(self, params=None):
        """
        Returns web domains information by its group id.

        Param:
            param -- Dictionary containing mail domain information.

        Output:
            Return a Dictionary with key/values with the mail domain parameter's values.
        """
        response = self._call("sites_web_domain_get", params)
        if response:
            return response
        else:
            return {"error": True, "type": "string", "detail": "web domain doesn't exist."}
