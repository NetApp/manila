# Copyright (c) 2014 Mirantis, Inc.
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
NetApp WFA client.

Contains classes required to issue api calls to WFA over REST.
"""
import time

import netaddr
from oslo_config import cfg
from oslo_log import log
import six
import six.moves.urllib.parse as parse

from manila import exception
from manila.i18n import _
from manila.share.drivers.netapp.wfa import base_api
from manila.share.drivers.netapp.wfa import wfa_constants as constants


WFA_OPTS_COMMON = [
    cfg.StrOpt('wfa_login',
               default='admin',
               help='User name for the WFA.'),
    cfg.StrOpt('wfa_password',
               help='Password for the WFA.',
               secret=True),
    cfg.StrOpt('wfa_endpoint',
               default=None,
               help='Host name or IP address for the WFA.'),
    cfg.IntOpt('check_job_delay',
               default=10,
               help='Delay in seconds for checking of job.'),
    cfg.IntOpt('max_attempts_check_job',
               default=20,
               help='Max attempts for checking of job.')
]


SUCCESSFUL_STATUS = ["PAUSED", "RUNNING", "PENDING",
                     "SCHEDULED", "EXECUTING", "PLANNING"]
DONE_STATUS = ["COMPLETED"]
FAILED_STATUS = ["FAILED", "ABORTING", "CANCELED", "OBSOLETE"]


CONF = cfg.CONF
CONF.register_opts(WFA_OPTS_COMMON)
LOG = log.getLogger(__name__)


class NaServer(base_api.BaseNaServer):
    """Encapsulates server connection logic."""

    SERVER_TYPE_WFA = 'wfa'
    CONTENT_TYPE = 'application/xml'

    def __init__(self, host, username=None, password=None):
        super(NaServer, self).__init__(
            host,
            server_type=self.SERVER_TYPE_WFA,
            username=username,
            password=password)

    def _set_url(self):
        """Set the default url for server."""

    def _get_url(self):
        url = ('%(protocol)s://%(host)s:%(port)s')
        params = {'protocol': self._protocol,
                  'host': self._host,
                  'port': self._port}
        return url % params

    def _prepare_request(self, link, data):
        if data and not isinstance(data, base_api.NaElement):
            raise ValueError("NaElement must be supplied to invoke api")
        elif data:
            data = data.to_string(standalone=True)
        url = '%(address)s/rest/%(link)s'
        params = {'address': self._get_url(), 'link': link}
        return (url % params, data)

    def _get_result(self, response):
        """Get the NaElement for the response."""
        return self._parse_response(response)

    def add_user_inputs(self, na_element, inputs):
        """Add user inputs to NaElement.

        Example usage:
        <root>
          <userInputValues>
            <userInputEntry key="key1" value="vol1"/>
            <userInputEntry key="key2" value="vol2"/>
            <userInputEntry key="key3" value="vol3"/>
          </userInputValues>
        </root>

        The above can be achieved by doing
        inputs = {"key1": "val1",
                  "key2": "val2",
                  "key3": "val3"}
        root = base_api.NaElement('root')
        na_server.add_user_inputs(root, inputs)
        """
        if not isinstance(na_element, base_api.NaElement):
            raise ValueError("NaElement must be supplied to add_user_inputs")
        user_input_vals = base_api.NaElement('userInputValues')
        for inp_key, inp_val in six.iteritems(inputs):
            input_entry = base_api.NaElement('userInputEntry')
            input_entry.add_attrs(key=inp_key, value=inp_val)
            user_input_vals.add_child_elem(input_entry)
        na_element.add_child_elem(user_input_vals)


class WFAClient(object):
    """Client for WFA specific requests."""

    def __init__(self, *args, **kwargs):
        self.configuration = kwargs.get('configuration', None)
        if not self.configuration:
            raise exception.NetAppException(_("WFA configuration missing."))
        self.configuration.append_config_values(WFA_OPTS_COMMON)
        self._client = NaServer(
            host=self.configuration.wfa_endpoint,
            username=self.configuration.wfa_login,
            password=self.configuration.wfa_password,
        )
        self.workflow_inputs = {}
        self.workflows = {}

    def set_workflows(self, workflow_name_dict):
        self.workflows = self._get_workflow_list(workflow_name_dict)

    def set_workflow_inputs(self, workflow_input_dict):
        self.workflow_inputs = workflow_input_dict

    def send_request(self, url, data=None):
        try:
            return self._client.invoke_successfully(url, data)
        except base_api.NaApiError as error:
            if error.code in constants.FAILED_REQUEST_REASONS:
                params = {
                    'url': url,
                    'data': "" if data is None else data.to_string(),
                    'reason': ", ".join(
                        constants.FAILED_REQUEST_REASONS[error.code])
                }
                msg = _("Request was failed. Probable reasons are: %(reason)s."
                        " URL: %(url)s, Data: %(data)s.")
                raise exception.NetAppException(msg % params)
            else:
                raise

    def _parse_workflow_resp(self, response):
        """Parse response from workflow's execution."""
        ret_params = {}
        job_elements = ('jobStatus', 'scheduleType',
                        'plannedExecutionTime')

        ret_params['jobId'] = response.get_attr('jobId')
        job_info = response.get_child_by_name('jobStatus')

        workflow_exec_progress = job_info.get_child_by_name(
            'workflow-execution-progress')
        if workflow_exec_progress:
            ret_params['current-command'] = \
                workflow_exec_progress.get_child_by_name(
                    'current-command').get_content()
            ret_params['current-command-index'] = \
                workflow_exec_progress.get_child_by_name(
                    'current-command-index').get_content()
            ret_params['commands-number'] = \
                workflow_exec_progress.get_child_by_name(
                    'commands-number').get_content()

        for element in job_elements:
            result = job_info.get_child_by_name(element).get_content().strip()
            if result and result is not None:
                ret_params[element] = result

        try:
            out_params = response.get_child_by_name(
                'jobStatus').get_child_by_name(
                    'returnParameters').get_children()
        except AttributeError:
            # In workflow execution case this node will be skipped.
            out_params = []

        for element in out_params:
            key = element.get_attr('key')
            value = element.get_attr('value')
            if value and value is not None:
                ret_params[key] = value

        return ret_params

    def _send_workflow_request(self, workflow_uuid, inputs, comments=None):
        wf_input = base_api.NaElement('workflowInput')
        self._client.add_user_inputs(wf_input, inputs)
        if comments:
            wf_input.add_new_child("comments", comments)
        url = "workflows/%(uuid)s/jobs/" % {"uuid": workflow_uuid}
        response = self.send_request(url, wf_input)
        return self._parse_workflow_resp(response)

    def check_job_status(self, workflow_uuid, job_id):
        """Checks the job status for specified workflow.

        Generate of exception in failed case.
        """
        attempts = 0
        ret = None
        error = False

        url = "workflows/%(uuid)s/jobs/%(job_id)s"
        params = {"uuid": workflow_uuid, "job_id": job_id}
        while attempts < self.configuration.max_attempts_check_job:
            attempts += 1
            res = self.send_request(url % params)
            job_status_node = res.get_child_by_name('jobStatus')
            status = job_status_node.get_child_content('jobStatus')

            if status in DONE_STATUS:
                break
            elif status in FAILED_STATUS:
                ret = job_status_node.get_child_content(
                    'errorMessage')
                break
            elif status not in SUCCESSFUL_STATUS:
                ret = 'Unexpected job status: %s.' % status
                break
            time.sleep(self.configuration.check_job_delay)
        return_params = self._parse_workflow_resp(res)
        if status in SUCCESSFUL_STATUS:
            ret = "Not enough time for checking of job. "\
                  "Enlarge check_job_delay config option."
        if ret is not None:
            result = _("Job %(url)s was failed. Result: %(ret)s") % {
                'url': url % params, 'ret': ret}
            error = True
        else:
            result = _("Job %(job)s for workflow %(workflow)s has been "
                       "finished as %(status)s.") % {
                "job": job_id, "workflow": workflow_uuid, "status": status}
        return_params['result'] = result
        return_params['error'] = error
        return return_params

    def _get_workflow_list(self, workflow_name_dict):
        LOG.debug('Getting workflow list.')
        workflows = {}
        for method, workflow_name in workflow_name_dict.items():
            if not workflow_name:
                workflows[method] = None
                continue
            collection_tree = self.send_request(
                'workflows?name=' + parse.quote_plus(workflow_name))
            workflow_tree = collection_tree.get_children()[0]
            workflows[method] = self._get_workflow_dict(workflow_tree)
        return workflows

    def _get_workflow_dict(self, workflow_tree):
            row = {
                'name': workflow_tree.get_child_content('name'),
                'uuid': workflow_tree.get_attr('uuid'),
                'user_input_list': [],
                'return_parameters': []
            }

            # get user input list
            user_input_list_tree = \
                workflow_tree.get_child_by_name('userInputList')

            if user_input_list_tree:
                user_input_list = user_input_list_tree.get_children()

                for user_input in user_input_list:
                    name = user_input.get_child_content('name')
                    mandatory = user_input.get_child_content('mandatory')
                    default_value = user_input.get_child_content(
                        'defaultValue')
                    allowed_values = []
                    allowed_values_tree = user_input.get_child_by_name(
                        'allowedValues')
                    if allowed_values_tree:
                        allowed_values_list = \
                            allowed_values_tree.get_children()
                        allowed_values = [child.get_content()
                                          for child in allowed_values_list]

                    row['user_input_list'].append({
                        'name': name,
                        'mandatory': mandatory,
                        'default_value': default_value,
                        'allowed_values': allowed_values})

            # get return parameters
            return_parameters_list_tree = \
                workflow_tree.get_child_by_name('returnParameters')
            if return_parameters_list_tree:
                return_parameters_list = \
                    return_parameters_list_tree.get_children()

                for return_parameter in return_parameters_list:
                    name = return_parameter.get_child_content('name')
                    row['return_parameters'].append(name)

            return row

    def validate_inputs(self, method, inputs):
        workflow = self.workflows[method]
        check_list = [inp for inp in workflow['user_input_list']]
        mandatory = [inp for inp in check_list if inp['mandatory'] == 'true']
        check_names = set(r['name'] for r in mandatory)
        if not check_names == check_names & set(inputs.keys()):
            msg = _("Inputs %(missing)s for %(method)s is missing.")
            missing_fields = check_names - set(inputs.keys())
            raise exception.NetAppException(msg % {'missing': missing_fields,
                                                   'method': method})
        allowed = dict((r['name'], r['allowed_values']) for r in check_list)
        for k, v in six.iteritems(inputs):
            data = {'val': v, 'key': k, 'allowed': six.text_type(allowed)}
            if k == self.workflow_inputs[constants.ACCESS_IP]:
                # ip address validation
                try:
                    netaddr.IPNetwork(v)
                    continue
                except netaddr.AddrFormatError:
                    msg = _("IP address '%(val)s' for "
                            "input '%(key)s' is not valid.")
            elif k not in allowed:
                msg = _("Not acceptable key '%(key)s' is provided. "
                        "Should be one of %(allowed)s.")
            elif allowed[k] and v not in allowed[k]:
                msg = _("Not acceptable value '%(val)s' for input '%(key)s'. "
                        "Should be one of %(allowed)s.")
            else:
                continue
            raise exception.NetAppException(msg % data)

    def execute_workflow(self, workflow_uuid, inputs, comments, method):
        """Provide an execution of workflow.

        Also job status will be checked and response will be parsed.
        Args:
            workflow_uuid (str): UUId of executed workflow.
            inputs (dict): Input values for execution.
                Example:
                    {"volName": "name",
                     "volSize": "1",
                     "protocol": "NFS"}
            method(str): Executed operation ('create_share',
                'delete_share', etc.)
        Returns:
            NaElement generated from response.
        """
        self.validate_inputs(method, inputs)
        response = self._send_workflow_request(workflow_uuid,
                                               inputs,
                                               comments)
        LOG.debug("Result of execution (%(login)s@%(endpoint)s) for workflow "
                  "%(workflow)s: %(result)s",
                  {
                      "endpoint": self.configuration.wfa_endpoint,
                      "workflow": self.workflows[method]["name"],
                      "result": response,
                      "login": self.configuration.wfa_login,
                  })
        ret_params = self.check_job_status(workflow_uuid,
                                           response.get("jobId"))
        return ret_params

    def check_workflow_results(self, results, msg=None):
        """Parse results of workflow.

        Args:
            results (dict): Result of _execute_workflow.
            Example:
                {'result': _("Job some_url was failed. Result: some_bug"),
                 'error': True,
                 'jobId': 1,
                 'jobStatus': 'FAILED'}
                or
                {'result': _("Job for workflow ID has been finished as ..."),
                 'error': False,
                 'jobId': 2,
                 'jobStatus': 'COMPLETED'}
        Returns: None
        Raises:
            NetAppException in results['error'] == True case.
        """
        if results['error']:
            message = results['result']
            if msg is not None:
                message = ' '.join((results['result'], msg))
            raise exception.NetAppException(message)
        else:
            LOG.debug(results['result'])
