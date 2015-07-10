# Copyright (c) 2014 NetApp, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
NetApp api for ONTAP and OnCommand DFM.

Contains classes required to issue api calls to ONTAP and OnCommand DFM.
"""

from lxml import etree
from oslo_log import log
from six.moves import urllib

from manila.i18n import _

LOG = log.getLogger(__name__)


class BaseNaServer(object):
    """Encapsulates server connection logic."""

    TRANSPORT_TYPE_HTTP = 'http'
    TRANSPORT_TYPE_HTTPS = 'https'
    STYLE_LOGIN_PASSWORD = 'basic_auth'
    STYLE_CERTIFICATE = 'certificate_auth'
    CONTENT_TYPE = 'text/xml'

    def __init__(self, host, server_type=None,
                 transport_type=None,
                 style=None, username=None,
                 password=None):
        self._host = host
        transport_type = transport_type or self.TRANSPORT_TYPE_HTTP
        style = style or self.STYLE_LOGIN_PASSWORD

        if server_type is None:
            raise NaApiError(_('Server type should be declared.'))
        self.set_server_type(server_type)
        self.set_transport_type(transport_type)
        self.set_style(style)
        self._username = username
        self._password = password
        self._refresh_conn = True

    def get_transport_type(self):
        """Get the transport type protocol."""
        return self._protocol

    def set_default_port(self):
        """Set the server communication port by default."""
        self.set_port(80)

    def set_transport_type(self, transport_type):
        """Set the transport type protocol for api.

        Supports http and https transport types.
        """
        if transport_type.lower() not in (
                self.TRANSPORT_TYPE_HTTP,
                self.TRANSPORT_TYPE_HTTPS):
            raise ValueError('Unsupported transport type')
        self._protocol = transport_type.lower()
        self.set_default_port()
        self._refresh_conn = True

    def get_style(self):
        """Get the authorization style for communicating with the server."""
        return self._auth_style

    def set_style(self, style):
        """Set the authorization style for communicating with the server.

        Supports basic_auth for now. Certificate_auth mode to be done.
        """
        if style.lower() not in (self.STYLE_LOGIN_PASSWORD,
                                 self.STYLE_CERTIFICATE):
            raise ValueError('Unsupported authentication style')
        self._auth_style = style.lower()

    def get_server_type(self):
        """Get the target server type."""
        return self._server_type

    def _check_server_type(self, server_type):
        """Check the server type."""

    def _set_url(self):
        """Set the default url for server."""
        raise NotImplementedError()

    def set_server_type(self, server_type):
        """Set the target server type.

        Supports filer and dfm server types.
        """
        self._check_server_type(server_type)
        self._server_type = server_type.lower()
        self._set_url()
        self._refresh_conn = True

    def set_api_version(self, major, minor):
        """Set the api version."""

    def get_api_version(self):
        """Gets the api version tuple."""
        return None

    def set_port(self, port):
        """Set the server communication port."""
        try:
            int(port)
        except ValueError:
            raise ValueError('Port must be integer')
        self._port = str(port)
        self._refresh_conn = True

    def get_port(self):
        """Get the server communication port."""
        return self._port

    def set_timeout(self, seconds):
        """Sets the timeout in seconds."""
        try:
            self._timeout = int(seconds)
        except ValueError:
            raise ValueError('timeout in seconds must be integer')

    def get_timeout(self):
        """Gets the timeout in seconds if set."""
        if hasattr(self, '_timeout'):
            return self._timeout
        return None

    def get_vserver(self):
        """Get the vserver to use in tunneling."""
        return self._vserver

    def set_vserver(self, vserver):
        """Set the vserver to use if tunneling gets enabled."""
        self._vserver = vserver

    def set_username(self, username):
        """Set the user name for authentication."""
        self._username = username
        self._refresh_conn = True

    def set_password(self, password):
        """Set the password for authentication."""
        self._password = password
        self._refresh_conn = True

    def _prepare_request(self, *args, **kwargs):
        """Prepare some data for request.

        Should return correct url and data.
        At this step data should be converted to string.
        """
        raise NotImplementedError()

    def invoke_elem(self, *args, **kwargs):
        """Invoke the api on the server."""
        (url, data) = self._prepare_request(*args, **kwargs)
        request = self._create_request(url, data)
        if not hasattr(self, '_opener') or not self._opener \
                or self._refresh_conn:
            self._build_opener()
        try:
            if hasattr(self, '_timeout'):
                response = self._opener.open(request, timeout=self._timeout)
            else:
                response = self._opener.open(request)
        except urllib.error.HTTPError as e:
            raise NaApiError(e.code, e.msg)
        except Exception as e:
            raise NaApiError('Unexpected error', e)
        xml = response.read()
        return self._get_result(xml)

    def invoke_successfully(self, *args, **kwargs):
        """Invokes api."""

        return self.invoke_elem(*args, **kwargs)

    def _create_request(self, url, data):
        """Creates request in the desired format."""
        request = urllib.request.Request(
            url, data=data,
            headers={'Content-Type': self.CONTENT_TYPE, 'charset': 'utf-8'})
        return request

    def _parse_response(self, response):
        """Get the NaElement for the response."""
        if not response:
            raise NaApiError('No response received')
        xml = etree.XML(response)
        return NaElement(xml)

    def _get_result(self, response):
        """Gets the call result."""
        raise NotImplementedError()

    def _get_url(self):
        raise NotImplementedError()

    def _build_opener(self):
        if self._auth_style == self.STYLE_LOGIN_PASSWORD:
            auth_handler = self._create_basic_auth_handler()
        else:
            auth_handler = self._create_certificate_auth_handler()
        opener = urllib.request.build_opener(auth_handler)
        self._opener = opener

    def _create_basic_auth_handler(self):
        password_man = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_man.add_password(None, self._get_url(), self._username,
                                  self._password)
        auth_handler = urllib.request.HTTPBasicAuthHandler(password_man)
        return auth_handler

    def _create_certificate_auth_handler(self):
        raise NotImplementedError()

    def __str__(self):
        return "server: %s" % (self._host)


class NaElement(object):
    """Class wraps basic building block for NetApp api request."""

    def __init__(self, name):
        """Name of the element or etree.Element."""
        if isinstance(name, etree._Element):
            self._element = name
        else:
            self._element = etree.Element(name)

    def get_name(self):
        """Returns the tag name of the element."""
        return self._element.tag

    def set_content(self, text):
        """Set the text string for the element."""
        self._element.text = text

    def get_content(self):
        """Get the text for the element."""
        return self._element.text

    def add_attr(self, name, value):
        """Add the attribute to the element."""
        self._element.set(name, value)

    def add_attrs(self, **attrs):
        """Add multiple attributes to the element."""
        for attr in attrs.keys():
            self._element.set(attr, attrs.get(attr))

    def add_child_elem(self, na_element):
        """Add the child element to the element."""
        if isinstance(na_element, NaElement):
            self._element.append(na_element._element)
            return
        raise

    def get_child_by_name(self, name):
        """Get the child element by the tag name."""
        for child in self._element.iterchildren():
            if child.tag == name or etree.QName(child.tag).localname == name:
                return NaElement(child)
        return None

    def get_child_content(self, name):
        """Get the content of the child."""
        for child in self._element.iterchildren():
            if child.tag == name or etree.QName(child.tag).localname == name:
                return child.text
        return None

    def get_children(self):
        """Get the children for the element."""
        return [NaElement(el) for el in self._element.iterchildren()]

    def has_attr(self, name):
        """Checks whether element has attribute."""
        attributes = self._element.attrib or {}
        return name in attributes.keys()

    def get_attr(self, name):
        """Get the attribute with the given name."""
        attributes = self._element.attrib or {}
        return attributes.get(name)

    def get_attr_names(self):
        """Returns the list of attribute names."""
        attributes = self._element.attrib or {}
        return attributes.keys()

    def add_new_child(self, name, content, convert=False):
        """Add child with tag name and context.

        Convert replaces entity refs to chars.
        """
        child = NaElement(name)
        if convert:
            content = NaElement._convert_entity_refs(content)
        child.set_content(content)
        self.add_child_elem(child)

    @staticmethod
    def _convert_entity_refs(text):
        """Converts entity refs to chars to handle etree auto conversions."""
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        return text

    @staticmethod
    def create_node_with_children(node, **children):
        """Creates and returns named node with children."""
        parent = NaElement(node)
        for child in children.keys():
            parent.add_new_child(child, children.get(child, None))
        return parent

    def add_node_with_children(self, node, **children):
        """Creates named node with children."""
        parent = NaElement.create_node_with_children(node, **children)
        self.add_child_elem(parent)

    def to_string(self, pretty=False, method='xml', encoding='UTF-8',
                  standalone=False):
        """Prints the element to string."""
        return etree.tostring(self._element, method=method, encoding=encoding,
                              pretty_print=pretty,
                              standalone=standalone)

    def __getitem__(self, key):
        """Dict getter method for NaElement.

           Returns NaElement list if present,
           text value in case no NaElement node
           children or attribute value if present.
        """

        child = self.get_child_by_name(key)
        if child:
            if child.get_children():
                return child
            else:
                return child.get_content()
        elif self.has_attr(key):
            return self.get_attr(key)
        raise KeyError(_('No element by given name %s.') % (key))

    def __setitem__(self, key, value):
        """Dict setter method for NaElement.

           Accepts dict, list, tuple, str, int, float and long as valid value.
        """
        if key:
            if value:
                if isinstance(value, NaElement):
                    child = NaElement(key)
                    child.add_child_elem(value)
                    self.add_child_elem(child)
                elif isinstance(value, (str, int, float, long)):
                    self.add_new_child(key, str(value))
                elif isinstance(value, (list, tuple, dict)):
                    child = NaElement(key)
                    child.translate_struct(value)
                    self.add_child_elem(child)
                else:
                    raise TypeError(_('Not a valid value for NaElement.'))
            else:
                self.add_child_elem(NaElement(key))
        else:
            raise KeyError(_('NaElement name cannot be null.'))

    def translate_struct(self, data_struct):
        """Convert list, tuple, dict to NaElement and appends.

           Example usage:
           1.
           <root>
               <elem1>vl1</elem1>
               <elem2>vl2</elem2>
               <elem3>vl3</elem3>
           </root>
           The above can be achieved by doing
           root = NaElement('root')
           root.translate_struct({'elem1': 'vl1', 'elem2': 'vl2',
                                  'elem3': 'vl3'})
           2.
           <root>
               <elem1>vl1</elem1>
               <elem2>vl2</elem2>
               <elem1>vl3</elem1>
           </root>
           The above can be achieved by doing
           root = NaElement('root')
           root.translate_struct([{'elem1': 'vl1', 'elem2': 'vl2'},
                                  {'elem1': 'vl3'}])
        """
        if isinstance(data_struct, (list, tuple)):
            for el in data_struct:
                if isinstance(el, (list, tuple, dict)):
                    self.translate_struct(el)
                else:
                    self.add_child_elem(NaElement(el))
        elif isinstance(data_struct, dict):
            for k in data_struct.keys():
                child = NaElement(k)
                if isinstance(data_struct[k], (dict, list, tuple)):
                    child.translate_struct(data_struct[k])
                else:
                    if data_struct[k]:
                        child.set_content(str(data_struct[k]))
                self.add_child_elem(child)
        else:
            raise ValueError(_('Type cannot be converted into NaElement.'))


class NaApiError(Exception):
    """Base exception class for NetApp api errors."""

    def __init__(self, code='unknown', message='unknown'):
        self.code = code
        self.message = message

    def __str__(self, *args, **kwargs):
        return 'NetApp api failed. Reason - %s:%s' % (self.code, self.message)
