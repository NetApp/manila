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
""" NetApp Workflow Automation (WFA) proxy driver. """

import functools

from oslo_config import cfg
from oslo_log import log
import six

from manila import exception
from manila.i18n import _, _LW
from manila.share import driver
from manila.share.drivers.netapp.wfa import wfa_client
from manila.share.drivers.netapp.wfa import wfa_constants as constants
from manila.share import share_types
from manila import utils as manila_utils

WORKFLOWS_NAME_TMPL = {
    'wfa_create_share': 'os_create_nfs_share_%s',
    'wfa_delete_share': 'os_delete_nfs_share_%s',
    'wfa_create_snapshot': 'os_create_snapshot_%s',
    'wfa_delete_snapshot': 'os_delete_snapshot_%s',
    'wfa_create_share_from_snapshot': 'os_create_nfs_share_snapshot_%s',
    'wfa_allow_access': 'os_allow_access_%s',
    'wfa_deny_access': 'os_deny_access_%s'
}

WFA_OPTS = [
    cfg.StrOpt(constants.ACCESS_IP,
               default=constants.WORKFLOW_INPUT_NAMES[
                   constants.ACCESS_IP],
               help='Name of the Access IP input variable for a workflow.'),
    cfg.StrOpt(constants.AGGREGATE_NAME,
               default=constants.WORKFLOW_INPUT_NAMES[
                   constants.AGGREGATE_NAME],
               help='Name of the aggregate input variable for a workflow.'),
    cfg.StrOpt(constants.CLUSTER_NAME,
               default=constants.WORKFLOW_INPUT_NAMES[constants.CLUSTER_NAME],
               help='Name of the cluster input variable for a workflow.'),
    cfg.StrOpt(constants.LEVEL_OF_ACCESS,
               default=constants.WORKFLOW_INPUT_NAMES[
                   constants.LEVEL_OF_ACCESS],
               help='Name of the level of access '
                    'input variable for a workflow.'),
    cfg.StrOpt(constants.SNAPSHOT_NAME,
               default=constants.WORKFLOW_INPUT_NAMES[constants.SNAPSHOT_NAME],
               help='Name of the snapshot input variable for a workflow.'),
    cfg.StrOpt(constants.VOLUME_NAME,
               default=constants.WORKFLOW_INPUT_NAMES[constants.VOLUME_NAME],
               help='Name of the volume input variable for a workflow.'),
    cfg.StrOpt(constants.VOLUME_SIZE,
               default=constants.WORKFLOW_INPUT_NAMES[constants.VOLUME_SIZE],
               help='Name of the volume size input variable for a workflow.'),
    cfg.StrOpt(constants.VSERVER_NAME,
               default=constants.WORKFLOW_INPUT_NAMES[constants.VSERVER_NAME],
               help='Name of the vserver input variable for a workflow.'),
    cfg.StrOpt('wfa_series_id',
               help='The part of workflows names (depends on backend).'),
    cfg.StrOpt('wfa_create_share',
               default=WORKFLOWS_NAME_TMPL['wfa_create_share'],
               help='Name of the workflow for creation of a share.'),
    cfg.StrOpt('wfa_delete_share',
               default=WORKFLOWS_NAME_TMPL['wfa_delete_share'],
               help='Name of the workflow for deletion of a share.'),
    cfg.StrOpt('wfa_create_snapshot',
               default=WORKFLOWS_NAME_TMPL['wfa_create_snapshot'],
               help='Name of the workflow for creation of a shapshot.'),
    cfg.StrOpt('wfa_delete_snapshot',
               default=WORKFLOWS_NAME_TMPL['wfa_delete_snapshot'],
               help='Name of the workflow for deletion of a shapshot.'),
    cfg.StrOpt('wfa_create_share_from_snapshot',
               default=WORKFLOWS_NAME_TMPL['wfa_create_share_from_snapshot'],
               help='Name of the workflow for creation '
                    'of a share from snapshot.'),
    cfg.StrOpt('wfa_allow_access',
               default=WORKFLOWS_NAME_TMPL['wfa_allow_access'],
               deprecated_name='wfa_access_allow',
               help='Name of the workflow for share access allow operation.'),
    cfg.StrOpt('wfa_deny_access',
               default=WORKFLOWS_NAME_TMPL['wfa_deny_access'],
               deprecated_name='wfa_access_deny',
               help='Name of the workflow for share access deny operation.'),
    cfg.StrOpt('wfa_share_name_template',
               default='manila_%(share_id)s',
               help='Template for share name using WFA. '
                    'Expected one point of replacement.'),
    cfg.StrOpt('wfa_snapshot_name_template',
               default='manila_%(snapshot_id)s_snapshot',
               help='Template for snapshot name using WFA. '
                    'Expected one point of replacement.'),
    cfg.DictOpt('wfa_extra_configuration',
                default={},
                help='Extra options that will be used instead of extra spec '
                     'in missing case. '
                     'Example: clusName:val,aggrName:val,vserverName:val'),
]

CONF = cfg.CONF
CONF.register_opts(WFA_OPTS)
LOG = log.getLogger(__name__)


def synchronized_operation(f):

    @functools.wraps(f)
    def wrapped_func(self, *args, **kwargs):
        share_id = ''
        snapshot_id = ''
        method_name = f.__name__

        if method_name == 'delete_share':
            share_id = args[1]['id']
        elif method_name == 'create_snapshot':
            share_id = args[1]['share_id']
        elif method_name == 'delete_snapshot':
            snapshot_id = args[1]['id']
        elif method_name == 'create_share_from_snapshot':
            snapshot_id = args[2]['id']
        else:
            raise exception.NetAppException(
                'Unrecognized operation %s for synchronization.' %
                method_name)

        if share_id:
            lock_name = 'lock_during_delete_share-%s' % share_id
        elif snapshot_id:
            lock_name = 'lock_during_delete_snapshot-%s' % snapshot_id

        @manila_utils.synchronized(lock_name, external=True)
        def source_func(self, *args, **kwargs):
            return f(self, *args, **kwargs)

        return source_func(self, *args, **kwargs)

    return wrapped_func


def check_workflow_availability_for_action(f):
    def wrap(self, *args, **kwargs):
        method_name = f.__name__
        try:
            workflow = self._client.workflows[method_name]
        except KeyError:
            raise exception.NetAppException(
                _('Unexpected method name: %s.') % method_name)

        if workflow is None:
            wf_name_tmpl = WORKFLOWS_NAME_TMPL['_'.join(('wfa', method_name))]
            wf_name = wf_name_tmpl % self.configuration.wfa_series_id
            raise exception.NetAppException(_(
                'Workflow for action %(action)s was not found. '
                'Please, specify correct workflow name in the config file or '
                'use default name %(default_workflow)s for workflow.') %
                {'action': method_name, 'default_workflow': wf_name})
        else:
            return f(self, *args, **kwargs)
    return wrap


class NetAppWFADriver(driver.ShareDriver):
    """NetApp Workflow Automation (WFA) proxy driver."""

    def __init__(self, *args, **kwargs):
        super(NetAppWFADriver, self).__init__(False, *args, **kwargs)

        self.private_storage = kwargs['private_storage']
        self._licenses = []
        self._client = None
        if self.configuration:
            self.configuration.append_config_values(WFA_OPTS)
        self.backend_name = self.configuration.safe_get(
            'share_backend_name') or 'NetApp_WFA'

        self.workflow_inputs = {}
        self.workflow_name_dict = {}

    def ensure_share(self, context, share, share_server=None):
        """Invoked to sure that share is exported."""
        pass

    def do_setup(self, context):
        """Prepare the driver.

        Called once by the manager after the driver is loaded.
        Sets up clients, sets up workflows.
        """
        self._client = wfa_client.WFAClient(configuration=self.configuration)
        if self.configuration.wfa_series_id is None:
            raise exception.NetAppException(_(
                'Config option wfa_series_id should be defined.'))

        self._workflow_setup()
        self._client.set_workflows(self.workflow_name_dict)

    def _workflow_setup(self):
        self._initialize_workflow_inputs()

        # get methods to workflows relations
        for method in ['create_share', 'delete_share', 'create_snapshot',
                       'delete_snapshot', 'create_share_from_snapshot',
                       'allow_access', 'deny_access']:
            workflow_tpl = getattr(self.configuration, 'wfa_' + method)
            try:
                workflow_name = workflow_tpl % self.configuration.wfa_series_id
            except TypeError:
                workflow_name = workflow_tpl
            self.workflow_name_dict[method] = workflow_name

    def _initialize_workflow_inputs(self):
        for input_name in constants.WORKFLOW_INPUT_NAMES:
            config_input_name = getattr(self.configuration, input_name)
            self.workflow_inputs[input_name] = config_input_name

        self._client.set_workflow_inputs(self.workflow_inputs)

    def _get_wfa_share_name(self, share_id):
        """Returns share name for WFA service.

        It will be generated from share uuid and wfa_share_name_template.
        """
        share_id = share_id.replace('-', '_')
        return (self.configuration.wfa_share_name_template %
                {'share_id': share_id})

    def _get_wfa_snapshot_name(self, snapshot_id):
        """Returns snapshot name for WFA service.

        It will be generated from snapshot uuid and
        wfa_snapshot_name_template.
        """
        snapshot_id = snapshot_id.replace('-', '_')
        return (self.configuration.wfa_snapshot_name_template %
                {'snapshot_id': snapshot_id})

    def _get_inputs_from_specs(self, share, operation):
        """Returns input params for workflow from specs.

           In missing extra specs case config options will be used.
           Args:
               share: Share.
               operation (str): Executed operation ('create_share', etc.)

           Returns:
               dict
               Example:
                   {'param_name': 'param_value', 'param2_name': 'param2_value'}
           Raises:
               NetAppException in missing options in config and specs case.
        """
        input_extra_specs = {}
        extra_specs = share_types.get_extra_specs_from_share(share)
        check = dict(constants.EXTRA_SPECS[operation])
        if set(check.keys()) != set(extra_specs.keys()) & set(check.keys()):
            missing = set(check.keys()) - set(extra_specs.keys())
            msg = 'Extra specs %s are missing and will be taken from config.'
            LOG.debug(msg, missing)
            for key in missing:
                param_name = key.split(':')[1]
                value = self.configuration.wfa_extra_configuration.get(
                    param_name, None)
                # We should check optionality of extra spec.
                # If spec is optional  and undefined it will be skipped.
                if value is None and check[key]:
                    raise exception.NetAppException(
                        _('For wfa_extra_configuration '
                          '%s is missing.') % param_name)
                elif value is None:
                    LOG.debug('%s is optional and undefined. '
                              'It will be skipped.',
                              param_name)
                else:
                    LOG.debug('Default config option %s will be used.',
                              param_name)
                    input_extra_specs[param_name] = value

        for k, v in six.iteritems(extra_specs):
            # Allow add all qualified extra specs
            if constants.SPECS_PREFIX in k:
                input_extra_specs[k.split(':')[1]] = v

        return input_extra_specs

    def _check_protocol(self, share):
        """Check the equality of protocol to NFS."""
        if share['share_proto'] != 'NFS':
            msg = _('Only NFS protocol is supported by WFA driver.')
            raise exception.NetAppException(msg)

    def _is_share_deleted(self, ret_params):
        if ret_params['jobStatus'] == 'FAILED':
            if (ret_params['current-command-index'] == '0' and
                    ret_params['commands-number'] == '0' or
                    'not found' in ret_params['result'] or
                    'No volume named' in ret_params['result']):
                return True
        return False

    @check_workflow_availability_for_action
    def create_share(self, context, share, share_server=None):
        """Creates new share."""
        self._check_protocol(share)
        operation = 'create_share'
        metadata_fields = ['jobId', 'jobStatus']
        workflow_uuid = self._client.workflows[operation]['uuid']
        name = self._get_wfa_share_name(share['id'])
        extra_inputs = self._get_inputs_from_specs(share, operation)

        inputs = {
            self.workflow_inputs[constants.VOLUME_NAME]: name,
            self.workflow_inputs[constants.VOLUME_SIZE]:
                six.text_type(share['size']),
            constants.PROTOCOL: 'NFS'
        }
        inputs.update(extra_inputs)
        comments = 'Creation of share from manila service'

        ret_params = self._client.execute_workflow(workflow_uuid, inputs,
                                                   comments, operation)

        metadata = dict((k, v) for k, v in six.iteritems(ret_params)
                        if k in metadata_fields)
        self.private_storage.update(share['id'], metadata)
        self._client.check_workflow_results(ret_params)
        try:
            return ret_params['export_location']
        except KeyError:
            msg = _('Export location was not returned.')
            raise exception.NetAppException(msg)

    @check_workflow_availability_for_action
    @synchronized_operation
    def delete_share(self, context, share, share_server=None):
        """Deletes share."""
        operation = 'delete_share'
        workflow_uuid = self._client.workflows[operation]['uuid']
        name = self._get_wfa_share_name(share['id'])
        inputs = {self.workflow_inputs[constants.VOLUME_NAME]: name}
        comments = 'Deletion of share from manila service'

        ret_params = self._client.execute_workflow(workflow_uuid, inputs,
                                                   comments, operation)
        try:
            self._client.check_workflow_results(ret_params)
        except exception.NetAppException:
            if self._is_share_deleted(ret_params):
                LOG.warning(_LW('Impossible to delete share %s. '
                                'Share does not exist at backend.'),
                            share['id'])
            else:
                raise

    @check_workflow_availability_for_action
    @synchronized_operation
    def create_snapshot(self, context, snapshot, share_server=None):
        """Creates a snapshot of a share."""
        operation = 'create_snapshot'
        workflow_uuid = self._client.workflows[operation]['uuid']
        share_name = self._get_wfa_share_name(snapshot['share_id'])
        snapshot_name = self._get_wfa_snapshot_name(snapshot['id'])

        inputs = {
            self.workflow_inputs[constants.VOLUME_NAME]: share_name,
            self.workflow_inputs[constants.SNAPSHOT_NAME]: snapshot_name,
        }
        comments = 'Creation of snapshot from share over manila service'
        ret_params = self._client.execute_workflow(workflow_uuid, inputs,
                                                   comments, operation)
        self._client.check_workflow_results(ret_params)

    @check_workflow_availability_for_action
    @synchronized_operation
    def create_share_from_snapshot(self, context, share, snapshot,
                                   share_server=None):
        """Creates a share from snapshot."""
        self._check_protocol(share)
        operation = 'create_share_from_snapshot'
        workflow_uuid = self._client.workflows[operation]['uuid']
        share_name = self._get_wfa_share_name(share['id'])
        snapshot_name = self._get_wfa_snapshot_name(snapshot['id'])
        metadata_fields = ['jobId', 'jobStatus']

        inputs = {
            self.workflow_inputs[constants.VOLUME_NAME]: share_name,
            self.workflow_inputs[constants.VOLUME_SIZE]:
                six.text_type(share['size']),
            constants.PROTOCOL: 'NFS',
            self.workflow_inputs[constants.SNAPSHOT_NAME]: snapshot_name,
        }
        comments = 'Creation of share from snapshot over manila service'
        ret_params = self._client.execute_workflow(workflow_uuid, inputs,
                                                   comments, operation)
        metadata = dict((k, v) for k, v in six.iteritems(ret_params)
                        if k in metadata_fields)
        self.private_storage.update(share['id'], metadata)
        self._client.check_workflow_results(ret_params)
        try:
            return ret_params['export_location']
        except KeyError:
            msg = _('Export location was not returned.')
            raise exception.NetAppException(msg)

    @check_workflow_availability_for_action
    @synchronized_operation
    def delete_snapshot(self, context, snapshot, share_server=None):
        """Deletes a snapshot of a share."""
        operation = 'delete_snapshot'
        workflow_uuid = self._client.workflows[operation]['uuid']
        snapshot_name = self._get_wfa_snapshot_name(snapshot['id'])

        inputs = {self.workflow_inputs[constants.SNAPSHOT_NAME]: snapshot_name}
        comments = 'Deletion of snapshot over manila service'
        ret_params = self._client.execute_workflow(workflow_uuid, inputs,
                                                   comments, operation)
        try:
            self._client.check_workflow_results(ret_params)
        except exception.NetAppException:
            if self._is_share_deleted(ret_params):
                LOG.warning(_LW('Impossible to delete snapshot %s. Snapshot '
                                'does not exist at backend.'), snapshot['id'])
            else:
                raise

    @check_workflow_availability_for_action
    def allow_access(self, context, share, access, share_server=None):
        """Allow access to a given share."""
        self._check_protocol(share)

        if access['access_type'] != 'ip':
            msg = _('Only IP access is supported by WFA driver.')
            raise exception.NetAppException(msg)

        operation = 'allow_access'
        workflow_uuid = self._client.workflows[operation]['uuid']
        name = self._get_wfa_share_name(share['id'])
        extra_inputs = self._get_inputs_from_specs(share, operation)
        inputs = {
            self.workflow_inputs[constants.ACCESS_IP]: access['access_to'],
            constants.PROTOCOL: 'NFS',
            self.workflow_inputs[constants.VOLUME_NAME]: name,
        }
        inputs.update(extra_inputs)
        comments = 'Allow access to a share from manila service'
        ret_params = self._client.execute_workflow(workflow_uuid, inputs,
                                                   comments, operation)
        self._client.check_workflow_results(ret_params)

    @check_workflow_availability_for_action
    def deny_access(self, context, share, access, share_server=None):
        """Denies access to a given share."""
        operation = 'deny_access'
        workflow_uuid = self._client.workflows[operation]['uuid']
        name = self._get_wfa_share_name(share['id'])
        inputs = {
            self.workflow_inputs[constants.ACCESS_IP]: access['access_to'],
            self.workflow_inputs[constants.VOLUME_NAME]: name
        }
        comments = 'Denies access to a share from manila service'
        ret_params = self._client.execute_workflow(workflow_uuid, inputs,
                                                   comments, operation)
        self._client.check_workflow_results(ret_params)

    def _update_share_stats(self, data=None):
        """Retrieve stats info from Data ONTAP backend."""

        LOG.debug('Updating share stats.')
        backend_name = self.configuration.safe_get('share_backend_name')
        data = {
            'share_backend_name': backend_name or 'NetApp_WFA',
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
        super(NetAppWFADriver, self)._update_share_stats(data=data)
