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

import mock

from manila import context
from manila import exception
from manila.share.drivers.netapp.wfa import base_api
from manila.share.drivers.netapp.wfa import wfa_client
from manila.share.drivers.netapp.wfa import wfa_constants as const
from manila import test
from manila.tests.share.drivers.netapp import fakes
from manila.tests.share.drivers.netapp.wfa import fakes as wfa_fakes


class WFAClientTestCase(test.TestCase):

    allow_access_workflow = {
        'allow_access': {
            'name': 'os_grant_ip_cdot',
            'return_parameters': [],
            'user_input_list': [{
                'allowed_values': ['some_expression'],
                'default_value': None,
                'mandatory': 'true',
                'name': 'accessIP'},
                {
                'allowed_values': ['any', 'cifs', 'nfs'],
                'default_value': 'any',
                'mandatory': 'false',
                'name': 'protocol'},
                {
                'allowed_values': [],
                'default_value': None,
                'mandatory': 'true',
                'name': 'volName'},
                {
                'allowed_values': ['ro', 'rw', 'su'],
                'default_value': None,
                'mandatory': 'true',
                'name': 'levelOfAccess'}
            ],
            'uuid': '4321-4321-4321-4321'
        }
    }

    def setUp(self):
        super(WFAClientTestCase, self).setUp()
        self._context = context.get_admin_context()
        self._db = mock.Mock()

        config = fakes.create_configuration_wfa()
        config.local_conf.set_override('check_job_delay', 0.001)

        self.client = wfa_client.WFAClient(configuration=config)

        for input_name in const.WORKFLOW_INPUT_NAMES:
            config_input_name = getattr(config, input_name)
            self.client.workflow_inputs[input_name] = config_input_name

    def test_validate_inputs_succes_correct_ip(self):
        operation = 'allow_access'
        self.client.workflows = self.allow_access_workflow
        ip_addr = '127.0.0.1'
        name = 'test_1234_1234_1234_1234'

        inputs = {
            self.client.workflow_inputs[const.ACCESS_IP]: ip_addr,
            "protocol": "nfs",
            self.client.workflow_inputs[const.VOLUME_NAME]: name,
            self.client.workflow_inputs[const.LEVEL_OF_ACCESS]: 'rw'
        }

        self.client.validate_inputs(operation, inputs)

    def test_validate_inputs_failed_invalid_ip(self):
        operation = 'allow_access'
        self.client.workflows = self.allow_access_workflow
        incorrect_ip_addr = '333.444.555.666'
        name = 'test_1234_1234_1234_1234'

        inputs = {
            self.client.workflow_inputs[const.ACCESS_IP]: incorrect_ip_addr,
            "protocol": "nfs",
            self.client.workflow_inputs[const.VOLUME_NAME]: name,
            self.client.workflow_inputs[const.LEVEL_OF_ACCESS]: 'rw'
        }

        self.assertRaises(
            exception.NetAppException,
            self.client.validate_inputs,
            operation,
            inputs
        )

    def test_validate_inputs_failed_invalid_cidr(self):
        operation = 'allow_access'
        self.client.workflows = self.allow_access_workflow
        incorrect_cidr = '127.0.0.1/999'
        name = 'test_1234_1234_1234_1234'

        inputs = {
            self.client.workflow_inputs[const.ACCESS_IP]: incorrect_cidr,
            "protocol": "nfs",
            self.client.workflow_inputs[const.VOLUME_NAME]: name,
            self.client.workflow_inputs[const.LEVEL_OF_ACCESS]: 'rw'
        }

        self.assertRaises(
            exception.NetAppException,
            self.client.validate_inputs,
            operation,
            inputs
        )

    def _check_job_status(self, status, message, error=True):
        self.client.configuration.max_attempts_check_job = 1
        uuid = 'fake_uuid'
        job_id = '1'
        response = """
        <job  jobId="1">
          <jobStatus>
            <jobStatus>%s</jobStatus>
            <scheduleType>Immediate</scheduleType>
            <errorMessage>res</errorMessage>
            <plannedExecutionTime>some_date</plannedExecutionTime>
            <returnParameters>
              <returnParameters key="export_path" value="/v8"/>
            </returnParameters>
          </jobStatus>
        </job>
        """ % status
        ret = self.client._client._parse_response(response)
        self.client.send_request = mock.Mock(
            return_value=ret)
        check = self.client.check_job_status(uuid, job_id)
        url = "workflows/%(uuid)s/jobs/%(job_id)s"
        params = {"uuid": uuid, "job_id": job_id}
        expected = {
            'jobStatus': status,
            'error': error,
            'export_path': '/v8',
            'jobId': job_id,
            'plannedExecutionTime': 'some_date',
            'result': message,
            'scheduleType': 'Immediate',
        }
        self.assertEqual(check, expected)
        self.client.send_request.assert_called_once_with(
            url % params)

    def test_check_job_status_failed(self):
        message = 'Job workflows/fake_uuid/jobs/1 was failed. '\
                  'Result: Not enough time for checking of job. '\
                  'Enlarge check_job_delay config option.'
        self._check_job_status('SCHEDULED', message)

    def test_check_job_status_failed2(self):
        message = 'Job workflows/fake_uuid/jobs/1 was failed. Result: res'
        self._check_job_status('FAILED', message)

    def test_check_job_status_success(self):
        message = 'Job 1 for workflow fake_uuid has been finished '\
                  'as COMPLETED.'
        self._check_job_status('COMPLETED', message, error=False)

    def test_send_request_success(self):
        url = 'fake_url'
        with mock.patch.object(self.client._client,
                               'invoke_successfully') as mock_invoke:
            mock_invoke.return_value = 'fake'
            ret = self.client.send_request(url)
            mock_invoke.assert_called_once_with(url, None)
            self.assertEqual(ret, 'fake')

    def _send_request_failed_error(self, message, code):
        url = 'fake_url'
        data = base_api.NaElement('fake')
        api_error = base_api.NaApiError(code=code)

        with mock.patch.object(self.client._client,
                               'invoke_successfully') as mock_invoke:
            mock_invoke.side_effect = api_error
            try:
                self.client.send_request(url, data)
            except exception.NetAppException as error:
                self.assertIn(message, error.msg)
                self.assertIn(url, error.msg)
            mock_invoke.assert_called_once_with(url, data)

    def test_send_request_failed_error_400(self):
        message = ('Request was failed. Probable reasons are: '
                   'the date format is not valid, the date for the '
                   'workflow is in the past, the user input value '
                   'was not provided in the right format, provided '
                   'user input is not defined for the workflow.')
        self._send_request_failed_error(message, 400)

    def test_send_request_failed_error_404(self):
        message = ('Request was failed. Probable reasons are: '
                   'the provided workflow uuid (job id) does not exist.')
        self._send_request_failed_error(message,
                                        404)

    def test_send_request_failed_error_401(self):
        message = ('Request was failed. Probable reasons are: '
                   'the client is not authenticated.')
        self._send_request_failed_error(message, 401)

    def test_get_workflow_list(self):
        with mock.patch.object(
                self.client, 'send_request') as mock_send_request:
            mock_send_request.side_effect = self._get_workflow_list_side_effect
            res = self.client._get_workflow_list(wfa_fakes.WORKFLOW_NAME_DICT)
            self.assertEqual("os_deny_ip_7m", res['deny_access']['name'])
            self.assertEqual("volName",
                             res['deny_access']['user_input_list'][0]['name'])
            self.assertEqual("os_create_nfs_share_snapshot_7m",
                             res['create_share_from_snapshot']['name'])

    def _get_workflow_list_side_effect(self, value):
        if value == ('workflows?name=' + 'os_deny_ip_7m'):
            return self.client._client. _parse_response(
                wfa_fakes.RAW_RESPONSE_LIST_OS_DENY_IP_7m)
        else:
            return self.client._client. _parse_response(
                wfa_fakes.RAW_RESPONSE_OS_CREATE_NFS_SHARE_SNAPSHOT_7M)

    def test_get_workflow_dict(self):
        na_elem_result = self.client._client._parse_response(
            wfa_fakes.RAW_RESPONSE_LIST_OS_DENY_IP_7m)
        res = self.client._get_workflow_dict(na_elem_result.get_children()[0])
        self.assertEqual("os_deny_ip_7m", res['name'])
        self.assertTrue('user_input_list' in res)
        self.assertEqual('volName', res['user_input_list'][0]['name'])

    def test_send_request_failed_error_500(self):
        url = 'fake_url'
        data = base_api.NaElement('fake')
        message = 'Fake_error.'
        api_error = base_api.NaApiError(message=message, code=500)
        with mock.patch.object(self.client._client,
                               'invoke_successfully') as mock_invoke:
            mock_invoke.side_effect = api_error
            try:
                self.client.send_request(url, data)
            except base_api.NaApiError as error:
                self.assertEqual(error.message, message)
            mock_invoke.assert_called_once_with(url, data)

    def test_execute_workflow(self):
        operation = 'fake'
        uuid = 'fake_uuid'
        self.client.workflows = {
            operation: {
                'uuid': uuid,
                'name': 'fake_workflow',
                'user_input_list': [
                    {'name': 'inp1',
                     'mandatory': 'true',
                     'allowed_values': ['val1']},
                    {'name': 'inp2',
                     'mandatory': 'true',
                     'allowed_values': ['val2']},
                ],
            }
        }
        inputs = {
            'inp1': 'val1',
            'inp2': 'val2',
        }
        comments = 'comments'
        self.client._send_workflow_request = mock.Mock(
            return_value={'jobId': 1})

        ret = {'some_ret': 'fake'}
        self.client.check_job_status = mock.Mock(
            return_value=ret)
        check = self.client.execute_workflow(
            uuid, inputs, comments, operation)
        self.client._send_workflow_request.assert_called_once_with(
            uuid, inputs, comments)
        self.client.check_job_status.assert_called_once_with(
            uuid, 1)
        self.assertEqual(ret, check)

    def test_execute_workflow_failed_inputs_check(self):
        operation = 'fake'
        uuid = 'fake_uuid'
        self.client.workflows = {
            operation: {
                'uuid': uuid,
                'user_input_list': [
                    {'name': 'inp1',
                     'mandatory': 'true',
                     'allowed_values': ['val1']},
                    {'name': 'inp2',
                     'mandatory': 'true',
                     'allowed_values': ['val2']},
                ],
            }
        }
        inputs = {
            'inp1': 'val1',
        }
        comments = 'comments'
        self.assertRaises(exception.NetAppException,
                          self.client.execute_workflow,
                          uuid, inputs, comments, operation)

    def test_execute_workflow_failed_inputs_check2(self):
        operation = 'fake'
        uuid = 'fake_uuid'
        self.client.workflows = {
            operation: {
                'uuid': uuid,
                'user_input_list': [
                    {'name': 'inp1',
                     'mandatory': 'true',
                     'allowed_values': ['val1']},
                    {'name': 'inp2',
                     'mandatory': 'true',
                     'allowed_values': ['val2']},
                ],
            }
        }
        inputs = {
            'inp1': 'val1',
            'inp2': 'wrong_val',
        }
        comments = 'comments'
        self.assertRaises(exception.NetAppException,
                          self.client.execute_workflow,
                          uuid, inputs, comments, operation)
