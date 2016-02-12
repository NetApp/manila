# Copyright (c) 2016 Chuck Fouts
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
NetApp WFA Workflow Integration Tests.

Tests the workflow, from the WFA driver, by mocking out the send_request method
in the WFA client. The WFA fakes file includes a dict with expected request
parameters, request uri, and workflow responses.
"""

from lxml import etree as ET
import mock
from oslo_config import cfg

from manila import context
from manila.share.drivers.netapp.wfa import base_api
from manila.share.drivers.netapp.wfa import wfa_client
from manila.share.drivers.netapp.wfa import wfa_constants as const
from manila.share.drivers.netapp.wfa import wfa_driver as driver
from manila import test
from manila.tests.share.drivers.netapp import fakes
from manila.tests.share.drivers.netapp.wfa import fakes as wfa_fakes

CONF = cfg.CONF


class NetAppWFAWorkflowTestCase(test.TestCase):

    def setUp(self):
        super(NetAppWFAWorkflowTestCase, self).setUp()
        self._context = context.get_admin_context()

        self._private_storage = mock.Mock()
        config = fakes.create_configuration_wfa()
        config.local_conf.set_override('driver_handles_share_servers', False)
        config.local_conf.set_override('share_backend_name',
                                       'fake_backend_name')

        self.driver = driver.NetAppWFADriver(
            private_storage=self._private_storage, configuration=config)

        self.driver.configuration.wfa_series_id = 'fake'
        self.driver.configuration.wfa_share_name_template = 'test_%(share_id)s'
        self.driver.configuration.wfa_snapshot_name_template = (
            'snap_%(snapshot_id)s')
        self.driver.configuration.wfa_extra_configuration = {
            const.CLUSTER_NAME: wfa_fakes.CLUSTER_NAME,
            const.AGGREGATE_NAME: wfa_fakes.AGGREGATE_NAME,
            const.VSERVER_NAME: wfa_fakes.VSERVER_NAME,
        }

        self.driver._client = wfa_client.WFAClient(configuration=config)
        self.send_request_mock = mock.Mock()
        self.driver._client.send_request = self.send_request_mock
        self.driver._workflow_setup()
        self.driver._client.workflows = wfa_fakes.WORKFLOW_LIST

    def _parse_fake_responses(self, fake_responses):
        responses = []
        for response in fake_responses:
            xml = ET.XML(response)
            responses.append(base_api.NaElement(xml))
        return responses

    def _verify_request_data(self, workflow_input, expected_inputs):
        """Pulls key value pairs from NaElement and compares with expected."""
        request_inputs = {}
        user_inputs = workflow_input.get_child_by_name('userInputValues')
        for child in user_inputs.get_children():
            request_inputs[child.get_attr('key')] = child.get_attr('value')

        self.assertEqual(expected_inputs, request_inputs)

    def test_create_share(self):
        share = {
            'id': '1234-1234-1234-1234',
            'size': 100,
            'share_proto': 'NFS',
            'share_type_id': 'fake_share_type_id',
        }

        workflow = wfa_fakes.CREATE_SHARE_WORKFLOW
        self.mock_object(driver.share_types, 'get_extra_specs_from_share',
                         mock.Mock(return_value={}))

        responses = self._parse_fake_responses(workflow['responses'])
        self.send_request_mock.side_effect = responses
        self.driver.create_share(self._context, share)

        self.send_request_mock.assert_has_calls(workflow['send_request_calls'])

        first_call_args = self.send_request_mock.call_args_list[0]
        workflow_input = first_call_args[0][1]
        expected_inputs = workflow['request_inputs']
        self._verify_request_data(workflow_input, expected_inputs)

    def test_delete_share(self):
        share = {
            'id': '1234-1234-1234-1234',
            'size': 100,
            'share_proto': 'NFS',
            'share_type_id': 'fake_share_type_id',
        }

        workflow = wfa_fakes.DELETE_SHARE_WORKFLOW
        self.mock_object(driver.share_types, 'get_extra_specs_from_share',
                         mock.Mock(return_value={}))

        responses = self._parse_fake_responses(workflow['responses'])
        self.send_request_mock.side_effect = responses
        self.driver.delete_share(self._context, share)

        self.send_request_mock.assert_has_calls(workflow['send_request_calls'])

        first_call_args = self.send_request_mock.call_args_list[0]
        workflow_input = first_call_args[0][1]
        expected_inputs = workflow['request_inputs']
        self._verify_request_data(workflow_input, expected_inputs)

    def test_create_snapshot(self):
        snapshot = {
            'id': '9999-9999-9999-9999',
            'share_id': '5678-5678-5678-5678',
        }

        workflow = wfa_fakes.CREATE_SNAPSHOT_WORKFLOW
        self.mock_object(driver.share_types, 'get_extra_specs_from_share',
                         mock.Mock(return_value={}))

        responses = self._parse_fake_responses(workflow['responses'])
        self.send_request_mock.side_effect = responses
        self.driver.create_snapshot(self._context, snapshot)

        self.send_request_mock.assert_has_calls(workflow['send_request_calls'])

        first_call_args = self.send_request_mock.call_args_list[0]
        workflow_input = first_call_args[0][1]
        expected_inputs = workflow['request_inputs']
        self._verify_request_data(workflow_input, expected_inputs)

    def test_delete_snapshot(self):
        snapshot = {
            'id': '9999-9999-9999-9999',
            'share_id': '5678-5678-5678-5678',
        }

        workflow = wfa_fakes.DELETE_SNAPSHOT_WORKFLOW
        self.mock_object(driver.share_types, 'get_extra_specs_from_share',
                         mock.Mock(return_value={}))

        responses = self._parse_fake_responses(workflow['responses'])
        self.send_request_mock.side_effect = responses
        self.driver.delete_snapshot(self._context, snapshot)

        self.send_request_mock.assert_has_calls(workflow['send_request_calls'])

        first_call_args = self.send_request_mock.call_args_list[0]
        workflow_input = first_call_args[0][1]
        expected_inputs = workflow['request_inputs']
        self._verify_request_data(workflow_input, expected_inputs)
