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
Constants for WFA API calls.

"""
# Names of inputs for workflows.
ACCESS_IP = "accessIP"
AGGREGATE_NAME = "aggrName"
CLUSTER_NAME = "clusName"
LEVEL_OF_ACCESS = "levelOfAccess"
SNAPSHOT_NAME = "snapName"
VOLUME_NAME = "volName"
VOLUME_SIZE = "volSize"
VSERVER_NAME = "vserverName"
PROTOCOL = "protocol"

WORKFLOW_INPUT_NAMES = {
    ACCESS_IP: "accessIP",
    AGGREGATE_NAME: "aggrName",
    CLUSTER_NAME: "clusName",
    LEVEL_OF_ACCESS: "levelOfAccess",
    SNAPSHOT_NAME: "snapName",
    VOLUME_NAME: "volName",
    VOLUME_SIZE: "volSize",
    VSERVER_NAME: "vserverName"
}


SPECS_PREFIX = "netapp:"

# Names for extra specs keys based on workflows inputs.
EXTRA_SPEC_CLUSTER_NAME = SPECS_PREFIX + CLUSTER_NAME
EXTRA_SPEC_AGGREGATE = SPECS_PREFIX + AGGREGATE_NAME
EXTRA_SPEC_VSERVER = SPECS_PREFIX + VSERVER_NAME
EXTRA_SPEC_SNAPSHOT_POLICY = SPECS_PREFIX + "SnapShotPolicy"
EXTRA_SPEC_SPACE_RESERVATION = SPECS_PREFIX + "SpaceReservation"
EXTRA_SPEC_DATA_PROTECTION = SPECS_PREFIX + "DataProtection"
EXTRA_SPEC_SECURITY_STYLE = SPECS_PREFIX + "SecurityStyle"
EXTRA_SPEC_LEVEL_OF_ACCESS = SPECS_PREFIX + LEVEL_OF_ACCESS

# Extra specs grouped by operations.
EXTRA_SPECS = {
    'create_share': [
        # (name_of_extra_spec, mandatory)
        (EXTRA_SPEC_CLUSTER_NAME, False),
        (EXTRA_SPEC_AGGREGATE, False),
        (EXTRA_SPEC_VSERVER, False),
    ],
    'allow_access': [
        (EXTRA_SPEC_LEVEL_OF_ACCESS, True)
    ]
}

FAILED_REQUEST_REASONS = {
    400: [
        "the date format is not valid",
        "the date for the workflow is in the past",
        "the user input value was not provided in the right format",
        "provided user input is not defined for the workflow",
    ],
    401: [
        "the client is not authenticated",
    ],
    404: [
        "the provided workflow uuid (job id) does not exist",
    ],
}
