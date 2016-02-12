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

import mock
from oslo_config import cfg

from manila import context
from manila import exception
from manila.share import driver as base_driver
from manila.share.drivers.netapp.wfa import wfa_constants as const
from manila.share.drivers.netapp.wfa import wfa_driver as driver
from manila import test
from manila.tests.share.drivers.netapp import fakes


CONF = cfg.CONF


class NetAppWFADriverTestCase(test.TestCase):

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
        super(NetAppWFADriverTestCase, self).setUp()
        self._context = context.get_admin_context()

        self._private_storage = mock.Mock()
        config = fakes.create_configuration_wfa()
        config.local_conf.set_override('driver_handles_share_servers', False)
        config.local_conf.set_override('share_backend_name',
                                       'fake_backend_name')

        self.driver = driver.NetAppWFADriver(
            private_storage=self._private_storage, configuration=config)
        self.driver._client = mock.Mock()

        self.share = {
            'id': '1234-1234-1234-1234',
            'size': 100,
            'share_proto': 'NFS',
            'share_type_id': 'fake_share_type_id',
        }

        self.snapshot = {
            'id': '9999-9999-9999-9999',
            'share_id': '5678-5678-5678-5678',
        }

        self.driver._initialize_workflow_inputs()

        self.driver.configuration.wfa_series_id = 'fake'
        self.driver.configuration.wfa_share_name_template = 'test_%(share_id)s'
        self.driver.configuration.wfa_snapshot_name_template = (
            'snap_%(snapshot_id)s')
        self.driver.configuration.wfa_extra_configuration = {
            const.CLUSTER_NAME: 'fake_cluster_name',
            const.AGGREGATE_NAME: 'fake_aggr',
            const.VSERVER_NAME: 'fake_vserver'
        }

        self.metadata_params = {
            'jobId': '111',
            'jobStatus': 'COMPLETED'
        }

        self.ret_params = {
            'error': False,
            'result': 'fake_result'
        }

        self.ret_params_failed = {
            'error': True,
            'result': 'fake_result'
        }

    def test_create_share_success(self):
        operation = 'create_share'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }

        export_path = {'export_location': '/fake/path'}
        values = self._collect_items(self.metadata_params,
                                     self.ret_params,
                                     export_path)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=dict(values))
        self.mock_object(driver.share_types,
                         'get_extra_specs_from_share',
                         mock.Mock(return_value={}))

        self.driver.create_share(self._context, self.share)

        inputs = {
            const.VOLUME_NAME: 'test_1234_1234_1234_1234',
            const.VOLUME_SIZE: str(self.share['size']),
            'protocol': 'NFS',
            const.VSERVER_NAME: 'fake_vserver',
            const.AGGREGATE_NAME: 'fake_aggr',
            const.CLUSTER_NAME: 'fake_cluster_name'
        }

        comments = 'Creation of share from manila service'

        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation)

        self._private_storage.update.assert_called_once_with(
            self.share['id'], self.metadata_params)

    def _failed_without_workflow(self, operation, *args):
        self.driver._client.workflows = {
            operation: None
        }

        self.assertRaises(
            exception.NetAppException,
            getattr(self.driver, operation),
            self._context,
            *args
        )

    def test_create_share_failed_without_workflow(self):
        operation = 'create_share'
        self._failed_without_workflow(operation, self.share)

    def test_create_share_failed_with_incorrect_proto(self):
        operation = 'create_share'
        self.share['share_proto'] = 'fake_proto'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        self.assertRaises(
            exception.NetAppException,
            self.driver.create_share,
            self._context,
            self.share
        )

    def test_create_share_failed_without_export_path(self):
        self.driver._client.workflows = {
            'create_share': {
                'uuid': '4321-4321-4321-4321'
            }
        }
        values = self._collect_items(self.metadata_params, self.ret_params)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=dict(values))

        self.mock_object(driver.share_types,
                         'get_extra_specs_from_share',
                         mock.Mock(return_value={}))

        self.assertRaises(
            exception.NetAppException,
            self.driver.create_share,
            self._context,
            self.share
        )

    def test_allow_access_success_with_valid_ip(self):
        operation = 'allow_access'
        self.driver._client.workflows = self.allow_access_workflow

        fake_access = {
            'access_to': '127.0.0.1',
            'access_type': 'ip',
        }
        self.driver.configuration.wfa_extra_configuration[
            const.LEVEL_OF_ACCESS] = 'rw'

        self.driver._client.execute_workflow = mock.Mock(
            return_value=self.ret_params)
        self.mock_object(driver.share_types,
                         'get_extra_specs_from_share',
                         mock.Mock(return_value={}))

        self.driver.allow_access(self._context, self.share, fake_access)
        inputs = {
            const.ACCESS_IP: fake_access['access_to'],
            'protocol': 'NFS',
            const.VOLUME_NAME: 'test_1234_1234_1234_1234',
            const.LEVEL_OF_ACCESS: 'rw'
        }
        comments = 'Allow access to a share from manila service'
        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation,
        )

    def test_allow_access_success_with_valid_cidr(self):
        operation = 'allow_access'
        self.driver._client.workflows = self.allow_access_workflow

        fake_access = {
            'access_to': '127.0.0.1/23',
            'access_type': 'ip',
        }
        self.driver.configuration.wfa_extra_configuration[
            const.LEVEL_OF_ACCESS] = 'rw'

        self.driver._client.execute_workflow = mock.Mock(
            return_value=self.ret_params)
        self.mock_object(driver.share_types,
                         'get_extra_specs_from_share',
                         mock.Mock(return_value={}))

        self.driver.allow_access(self._context, self.share, fake_access)

        inputs = {
            const.ACCESS_IP: fake_access['access_to'],
            'protocol': 'NFS',
            const.VOLUME_NAME: 'test_1234_1234_1234_1234',
            const.LEVEL_OF_ACCESS: 'rw',
        }
        comments = 'Allow access to a share from manila service'
        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation,
        )

    def test_allow_access_failed_without_workflow(self):
        operation = 'allow_access'
        fake_access = {}
        self._failed_without_workflow(operation, self.share, fake_access)

    def test_allow_access_with_incorrect_proto(self):
        operation = 'allow_access'
        self.share['share_proto'] = 'fake_proto'
        fake_access = {}
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        self.assertRaises(
            exception.NetAppException,
            self.driver.allow_access,
            self._context,
            self.share,
            fake_access
        )

    def test_allow_access_with_invalid_access_type(self):
        operation = 'allow_access'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        fake_access = {
            'access_to': '127.0.0.1',
            'access_type': 'not_ip',
        }

        self.assertRaises(
            exception.NetAppException,
            self.driver.allow_access,
            self._context,
            self.share,
            fake_access
        )

    def _collect_items(self, *args):
        values = []
        for a in args:
            values.extend(a.items())
        return values

    def test_deny_access(self):
        operation = 'deny_access'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        fake_access = {'access_to': '127.0.0.1'}
        val = self._collect_items(self.metadata_params, self.ret_params)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=dict(val))
        self.driver.deny_access(self._context, self.share, fake_access)

        comments = 'Denies access to a share from manila service'
        inputs = {
            const.ACCESS_IP: fake_access['access_to'],
            const.VOLUME_NAME: 'test_1234_1234_1234_1234'
        }

        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation)

    def test_deny_access_failed_without_workflow(self):
        operation = 'deny_access'
        fake_access = {}
        self._failed_without_workflow(operation, self.share, fake_access)

    def test_deny_access_failed(self):
        operation = 'deny_access'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        fake_access = {'access_to': '127.0.0.1'}

        self.driver._client.execute_workflow = mock.Mock(
            side_effect=exception.NetAppException)

        self.assertRaises(
            exception.NetAppException,
            self.driver.deny_access,
            self._context,
            self.share,
            fake_access
        )

    def test_delete_share(self):
        operation = 'delete_share'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        values = self._collect_items(self.metadata_params, self.ret_params)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=dict(values))

        self.driver.delete_share(self._context, self.share)

        inputs = {const.VOLUME_NAME: 'test_1234_1234_1234_1234'}
        comments = 'Deletion of share from manila service'
        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation)

    def test_delete_share_failed_without_workflow(self):
        operation = 'delete_share'
        self._failed_without_workflow(operation, self.share)

    def test_delete_share_failed_req(self):
        self.driver._client.workflows = {
            'delete_share': {
                'uuid': '4321-4321-4321-4321'
            }
        }

        self.driver._client.execute_workflow = mock.Mock(
            side_effect=exception.NetAppException)

        self.assertRaises(
            exception.NetAppException,
            self.driver.delete_share,
            self._context,
            self.share
        )

    def test_delete_share_failed_job(self):
        operation = 'delete_share'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }

        checked_message = ('fake_result Probably share '
                           'does not exist at backend.')
        self.driver._client.execute_workflow = mock.Mock(
            return_value=self.ret_params_failed)
        try:
            self.driver.delete_share(self._context, self.share)
        except exception.NetAppException as error:
            self.assertEqual(error.msg, checked_message)
        inputs = {const.VOLUME_NAME: 'test_1234_1234_1234_1234'}
        comments = 'Deletion of share from manila service'
        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation)

    def test_do_setup_failed_without_wfa_series_id(self):
        self.driver.configuration.wfa_series_id = None
        self.assertRaises(
            exception.NetAppException,
            self.driver.do_setup,
            self._context
        )

    def test_create_snapshot_success(self):
        operation = 'create_snapshot'
        self.driver._client.workflows = {
            'create_snapshot': {
                'uuid': '4321-4321-4321-4321'
            }
        }

        values = self._collect_items(self.metadata_params, self.ret_params)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=dict(values))
        self.driver.create_snapshot(self._context, self.snapshot)

        inputs = {
            const.VOLUME_NAME: 'test_5678_5678_5678_5678',
            const.SNAPSHOT_NAME: 'snap_9999_9999_9999_9999',
        }
        comments = 'Creation of snapshot from share over manila service'

        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows['create_snapshot']['uuid'],
            inputs,
            comments,
            operation)

    def test_create_snapshot_failed_without_workflow(self):
        operation = 'create_snapshot'
        self._failed_without_workflow(operation, self.snapshot)

    def test_create_snapshot_failed_job_check(self):
        operation = 'create_snapshot'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }

        values = self._collect_items(self.metadata_params,
                                     self.ret_params_failed)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=values)

        self.driver._client.check_workflow_results = mock.Mock(
            side_effect=exception.NetAppException)
        inputs = {
            const.VOLUME_NAME: 'test_5678_5678_5678_5678',
            const.SNAPSHOT_NAME: 'snap_9999_9999_9999_9999',
        }
        comments = 'Creation of snapshot from share over manila service'

        self.assertRaises(exception.NetAppException,
                          self.driver.create_snapshot,
                          self._context,
                          self.snapshot)

        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation)

        self.driver._client.check_workflow_results.assert_called_once_with(
            values)

    def test_create_share_from_snapshot_failed_protocol_check(self):
        operation = 'create_share_from_snapshot'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        self.share['share_proto'] = 'CIFS'
        self.assertRaises(exception.NetAppException,
                          self.driver.create_share_from_snapshot,
                          self._context,
                          self.share,
                          self.snapshot)
        self.share['share_proto'] = 'NFS'

    def test_create_share_from_snapshot_failed_job_check(self):
        operation = 'create_share_from_snapshot'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }

        values = self._collect_items(self.metadata_params,
                                     self.ret_params_failed)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=dict(values))

        inputs = {
            const.VOLUME_NAME: 'test_1234_1234_1234_1234',
            const.SNAPSHOT_NAME: 'snap_9999_9999_9999_9999',
            const.VOLUME_SIZE: '100',
            'protocol': 'NFS',
        }
        comments = 'Creation of share from snapshot over manila service'
        self.assertRaises(exception.NetAppException,
                          self.driver.create_share_from_snapshot,
                          self._context,
                          self.share,
                          self.snapshot)

        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation)

    def test_create_share_from_snapshot_success(self):
        operation = 'create_share_from_snapshot'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        export_path = {'export_location': '/fake/path'}
        values = self._collect_items(self.metadata_params,
                                     self.ret_params,
                                     export_path)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=dict(values))

        self.driver.create_share_from_snapshot(
            self._context, self.share, self.snapshot)

        inputs = {
            const.VOLUME_NAME: 'test_1234_1234_1234_1234',
            const.SNAPSHOT_NAME: 'snap_9999_9999_9999_9999',
            const.VOLUME_SIZE: '100',
            'protocol': 'NFS',
        }
        comments = 'Creation of share from snapshot over manila service'

        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation)

        self._private_storage.update.assert_called_once_with(
            self.share['id'], self.metadata_params)

    def test_create_share_from_snapshot_failed_without_workflow(self):
        operation = 'create_share_from_snapshot'
        self._failed_without_workflow(operation, self.snapshot)

    def test_create_share_from_snapshot_failed_export_path(self):
        operation = 'create_share_from_snapshot'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        values = self._collect_items(self.metadata_params, self.ret_params)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=dict(values))

        inputs = {
            const.VOLUME_NAME: 'test_1234_1234_1234_1234',
            const.SNAPSHOT_NAME: 'snap_9999_9999_9999_9999',
            const.VOLUME_SIZE: '100',
            'protocol': 'NFS',
        }
        comments = 'Creation of share from snapshot over manila service'

        self.assertRaises(exception.NetAppException,
                          self.driver.create_share_from_snapshot,
                          self._context,
                          self.share,
                          self.snapshot)

        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation)

    def test_delete_snapshot_failed_job_check(self):
        operation = 'delete_snapshot'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        values = self._collect_items(self.metadata_params,
                                     self.ret_params_failed)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=dict(values))

        inputs = {const.SNAPSHOT_NAME: 'snap_9999_9999_9999_9999'}
        comments = 'Deletion of snapshot over manila service'
        checked_message = ('fake_result Probably snapshot does '
                           'not exist at backend.')
        try:
            self.driver.delete_snapshot(self._context, self.snapshot)
        except exception.NetAppException as err:
            self.assertEqual(err.msg, checked_message)

        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation)

    def test_delete_snapshot_success(self):
        operation = 'delete_snapshot'
        self.driver._client.workflows = {
            operation: {
                'uuid': '4321-4321-4321-4321'
            }
        }
        values = self._collect_items(self.metadata_params, self.ret_params)
        self.driver._client.execute_workflow = mock.Mock(
            return_value=dict(values))

        self.driver.delete_snapshot(self._context, self.snapshot)

        inputs = {const.SNAPSHOT_NAME: 'snap_9999_9999_9999_9999'}
        comments = 'Deletion of snapshot over manila service'
        self.driver._client.execute_workflow.assert_called_once_with(
            self.driver._client.workflows[operation]['uuid'],
            inputs,
            comments,
            operation)

    def test_delete_snapshot_failed_without_workflow(self):
        operation = 'delete_snapshot'
        self._failed_without_workflow(operation, self.snapshot)

    def test_get_input_from_specs(self):
        operation = 'create_share'
        self.driver.configuration.wfa_extra_configuration = {
            'vserverName': 'fake_vserver1',
            'clusName': 'fake_cluster1',
            'aggrName': 'fake_aggr1',
        }
        specs = {
            'netapp:vserverName': 'fake_vserver2',
            'netapp:aggrName': 'fake_aggr2',
        }
        expected = {
            'vserverName': 'fake_vserver2',
            'aggrName': 'fake_aggr2',
            'clusName': 'fake_cluster1',
        }
        with mock.patch.object(driver.share_types,
                               'get_extra_specs_from_share',
                               mock.Mock(return_value={})) as mock_utils:
            mock_utils.return_value = specs
            input_from_specs = self.driver._get_inputs_from_specs(
                self.share, operation)
            self.assertEqual(input_from_specs, expected)
            mock_utils.assert_called_once_with(self.share)

    def test_get_input_from_specs_with_optional_param(self):
        operation = 'create_share'
        self.driver.configuration.wfa_extra_configuration = {
            'vserverName': 'fake_vserver1',
            'aggrName': 'fake_aggr1',
        }
        specs = {
            'netapp:vserverName': 'fake_vserver2',
            'netapp:aggrName': 'fake_aggr2',
        }
        expected = {
            'vserverName': 'fake_vserver2',
            'aggrName': 'fake_aggr2',
        }
        with mock.patch.object(driver.share_types,
                               'get_extra_specs_from_share',
                               mock.Mock()) as mock_utils:
            mock_utils.return_value = specs
            input_from_specs = self.driver._get_inputs_from_specs(
                self.share, operation)
            self.assertEqual(input_from_specs, expected)
            mock_utils.assert_called_once_with(self.share)

    def test_get_input_from_specs_failed(self):
        operation = 'allow_access'
        self.driver.configuration.wfa_extra_configuration = {}
        specs = {}
        with mock.patch.object(driver.share_types,
                               'get_extra_specs_from_share',
                               mock.Mock(return_value={})) as mock_utils:
            mock_utils.return_value = specs
            self.assertRaises(exception.NetAppException,
                              self.driver._get_inputs_from_specs,
                              self.share, operation)
            mock_utils.assert_called_once_with(self.share)

    def test_get_share_stats_no_refresh(self):
        fake_stats = 'fake_stats'
        self.driver._stats = fake_stats
        stats = self.driver.get_share_stats(False)
        self.assertEqual(fake_stats, stats)

    def test_update_share_stats(self):

        mock_super_update_share_stats = self.mock_object(
            base_driver.ShareDriver, '_update_share_stats')

        fake_stats = {}
        self.driver._update_share_stats(data=fake_stats)

        expected = {
            'share_backend_name': 'fake_backend_name',
            'vendor_name': 'NetApp',
            'driver_version': '1.0',
            'netapp_storage_family': 'wfa',
            'storage_protocol': 'NFS',
            'total_capacity_gb': 'unknown',
            'free_capacity_gb': 'unknown',
            'reserved_percentage': 0,
            'pools': [
                {
                    'pool_name': 'wfa',
                    'total_capacity_gb': 'unknown',
                    'free_capacity_gb': 'unknown',
                    'allocated_capacity_gb': 'unknown',
                    'QoS_support': False,
                    'reserved_percentage': 0,
                }
            ]

        }
        mock_super_update_share_stats.assert_called_once_with(data=expected)
