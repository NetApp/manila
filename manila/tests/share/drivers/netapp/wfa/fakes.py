# Copyright 2016 Chuck Fouts.
# All rights reserved.
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

from manila.share.drivers.netapp.wfa import wfa_constants as const


CLUSTER_NAME = 'fake_cluster_name'
AGGREGATE_NAME = 'fake_aggr'
VSERVER_NAME = 'fake_vserver'

WORKFLOW_NAME_DICT = {
    'deny_access': 'os_deny_ip_7m',
    'create_share_from_snapshot': 'os_create_nfs_share_snapshot_7m',
}

RAW_RESPONSE_LIST_OS_DENY_IP_7m = """<collection
xmlns:atom='http://www.w3.org/2005/Atom'>
<workflow uuid='71d8e699-b0c9-42a1-a67f-a57aab734a3d'>
<name>os_deny_ip_7m</name><certification>NONE</certification><version>
<major>1</major><minor>0</minor><revision>4</revision></version>
<categories><category>OS Workflows</category></categories>
<userInputList><userInput><name>volName</name><type>String</type>
<allowedValues/><mandatory>false</mandatory></userInput><userInput>
<name>accessIP</name><type>String</type><allowedValues/>
<mandatory>false</mandatory></userInput></userInputList><returnParameters/>
<atom:link rel='export' href=
'http://192.168.231.200/rest/dars/71d8e699-b0c9-42a1-a67f-a57aab734a3d'/>
<atom:link rel='self' href=
'http://192.168.231.200/rest/workflows/71d8e699-b0c9-42a1-a67f-a57aab734a3d'/>
<atom:link rel='preview' href='http://192.168.231.200/rest/workflows/
71d8e699-b0c9-42a1-a67f-a57aab734a3d/preview'/>
<atom:link rel='out-parameter' href='http://192.168.231.200/rest/workflows/
71d8e699-b0c9-42a1-a67f-a57aab734a3d/out'/>
<atom:link rel='execute' href='http://192.168.231.200/rest/workflows/
71d8e699-b0c9-42a1-a67f-a57aab734a3d/jobs'/>
<atom:link rel='list' href='http://192.168.231.200/rest/workflows'/>
</workflow></collection>
"""

RAW_RESPONSE_OS_CREATE_NFS_SHARE_SNAPSHOT_7M = """<collection
xmlns:atom='http://www.w3.org/2005/Atom'><workflow
uuid='cebbf690-ef64-4374-98ae-0443ad613142'>
<name>os_create_nfs_share_snapshot_7m</name><certification>NONE
</certification><version><major>1</major><minor>0</minor>
<revision>5</revision></version><categories><category>OS Workflows
</category></categories><userInputList><userInput><name>snapName
</name><type>String</type><allowedValues/><mandatory>false</mandatory>
</userInput><userInput><name>volName</name><type>String</type>
<allowedValues/><mandatory>false</mandatory></userInput><userInput>
<name>volSize</name><defaultValue>0</defaultValue><type>Number</type>
<allowedValues/><mandatory>false</mandatory></userInput><userInput>
<name>vserverName</name><defaultValue></defaultValue><type>Query</type>
<allowedValues/><mandatory>false</mandatory></userInput><userInput>
<name>protocol</name><defaultValue>nfs</defaultValue><type>Enum</type>
<allowedValues><value>CIFS</value><value>NFS</value><value>cifs</value>
<value>nfs</value></allowedValues><mandatory>false</mandatory>
</userInput></userInputList><returnParameters/><atom:link rel='export'
href='http://192.168.231.200/rest/dars
/cebbf690-ef64-4374-98ae-0443ad613142'/><atom:link rel='self'
href='http://192.168.231.200/rest/workflows
/cebbf690-ef64-4374-98ae-0443ad613142'/><atom:link rel='preview'
href='http://192.168.231.200/rest/workflows
/cebbf690-ef64-4374-98ae-0443ad613142/preview'/><atom:link
rel='out-parameter' href='http://192.168.231.200/rest/workflows
/cebbf690-ef64-4374-98ae-0443ad613142/out'/><atom:link rel='execute'
href='http://192.168.231.200/rest/workflows
/cebbf690-ef64-4374-98ae-0443ad613142/jobs'/><atom:link rel='list'
href='http://192.168.231.200/rest/workflows'/></workflow></collection>
"""


WORKFLOW_LIST = {
    "create_share": {
        "name": "os_create_nfs_share_7m",
        "return_parameters": [
            "export_location",
        ],
        "user_input_list": [
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "clusName"
            },
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "vserverName"
            },
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "aggrName"
            },
            {
                "allowed_values": [
                    "CIFS",
                    "NFS",
                    "cifs",
                    "nfs"
                ],
                "default_value": "nfs",
                "mandatory": "true",
                "name": "protocol"
            },
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "true",
                "name": "volName"
            },
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "true",
                "name": "volSize"
            },
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "deDupe"
            },
            {
                "allowed_values": [],
                "default_value": "'0 0 0'",
                "mandatory": "false",
                "name": "snapSched"
            }
        ],
        "uuid": "ea1a0d89-ab4e-4373-846d-bf4541efb1eb"
    },
    "create_share_from_snapshot": {
        "name": "os_create_nfs_share_snapshot_7m",
        "return_parameters": [],
        "user_input_list": [
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "snapName"
            },
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "volName"
            },
            {
                "allowed_values": [],
                "default_value": "0",
                "mandatory": "false",
                "name": "volSize"
            },
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "vserverName"
            },
            {
                "allowed_values": [
                    "CIFS",
                    "NFS",
                    "cifs",
                    "nfs"
                ],
                "default_value": "nfs",
                "mandatory": "false",
                "name": "protocol"
            }
        ],
        "uuid": "cebbf690-ef64-4374-98ae-0443ad613142"
    },
    "create_snapshot": {
        "name": "os_create_snapshot_7m",
        "return_parameters": [],
        "user_input_list": [
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "snapName"
            },
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "volName"
            }
        ],
        "uuid": "096d4f1d-aad0-4e23-973d-4302a0d2b8ad"
    },
    "delete_share": {
        "name": "os_delete_nfs_share_7m",
        "return_parameters": [],
        "user_input_list": [
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "volName"
            }
        ],
        "uuid": "f07d9097-1055-4a82-8326-822204f64111"
    },
    "delete_snapshot": {
        "name": "os_delete_snapshot_7m",
        "return_parameters": [],
        "user_input_list": [
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "snapName"
            }
        ],
        "uuid": "e25e0c9c-2c64-434a-8f00-e0d24f306df6"
    },
    "deny_access": {
        "name": "os_deny_ip_7m",
        "return_parameters": [],
        "user_input_list": [
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "volName"
            },
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "false",
                "name": "accessIP"
            }
        ],
        "uuid": "71d8e699-b0c9-42a1-a67f-a57aab734a3d"
    },
    "allow_access": {
        "name": "os_grant_ip_7m",
        "return_parameters": [],
        "user_input_list": [
            {
                "allowed_values": [
                    "[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\."
                    "[0-9]{1,3}\\/{0,1}[1-3]{0,1}[0-9]{0,1}"
                ],
                "default_value": None,
                "mandatory": "true",
                "name": "accessIP"
            },
            {
                "allowed_values": [],
                "default_value": None,
                "mandatory": "true",
                "name": "volName"
            },
            {
                "allowed_values": [
                    "ro",
                    "rw",
                    "su"
                ],
                "default_value": None,
                "mandatory": "true",
                "name": "levelOfAccess"
            },
            {
                "allowed_values": [
                    "CIFS",
                    "NFS",
                    "cifs",
                    "nfs"
                ],
                "default_value": "nfs",
                "mandatory": "false",
                "name": "protocol"
            }
        ],
        "uuid": "0feb07b4-a288-48ba-b01f-f4d12252831e"
    }
}

CREATE_SHARE_WORKFLOW = {
    'request_inputs': {
        const.CLUSTER_NAME: CLUSTER_NAME,
        const.AGGREGATE_NAME: AGGREGATE_NAME,
        const.VSERVER_NAME: VSERVER_NAME,
        const.PROTOCOL: "NFS",
        const.VOLUME_SIZE: "100",
        const.VOLUME_NAME: "test_1234_1234_1234_1234",
    },
    'send_request_calls': [
        mock.call('workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/',
                  mock.ANY),
        mock.call('workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909'),
        mock.call('workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909'),
    ],
    'responses': [
        """<job xmlns:atom='http://www.w3.org/2005/Atom' jobId='909'><workflow
    uuid='ea1a0d89-ab4e-4373-846d-bf4541efb1eb'><name>os_create_nfs_share_7m
    </name><description>Creates a volume and exports it over NFS. This
    workflow includes: - Creating a volume with the given name and size. The
    volume is created on a suitable aggregate found in the environment.
    </description><certification>NONE</certification><version><major>1</major>
    <minor>0</minor><revision>12</revision></version><categories><category>OS
    Workflows</category></categories><userInputList><userInput><name>clusName
    </name><type>String</type><allowedValues/><mandatory>false</mandatory>
    </userInput><userInput><name>vserverName</name><type>String</type>
    <allowedValues/><mandatory>false</mandatory></userInput><userInput>
    <name>aggrName</name><type>String</type><allowedValues/><mandatory>false
    </mandatory></userInput><userInput><name>protocol</name><defaultValue>nfs
    </defaultValue><type>Enum</type><allowedValues><value>CIFS</value>
    <value>NFS</value><value>cifs</value><value>nfs</value></allowedValues>
    <mandatory>true</mandatory></userInput><userInput><name>volName</name>
    <type>String</type><allowedValues/><mandatory>true</mandatory></userInput>
    <userInput><name>volSize</name><defaultValue></defaultValue><type>Number
    </type><allowedValues/><mandatory>true</mandatory></userInput><userInput>
    <name>deDupe</name><type>String</type><allowedValues/><mandatory>false
    </mandatory></userInput><userInput><name>snapSched</name><defaultValue>
    '0 0 0'</defaultValue><type>String</type><allowedValues/><mandatory>
    false</mandatory></userInput></userInputList><returnParameters>
    <returnParameter><name>export_location</name><value>
    ((($aggrName != &quot;&quot;) &amp;&amp; ($clusName != &quot;&quot;)
    &amp;&amp; ($vserverName != &quot;&quot;)) ? volume.vfiler.ip_address :
    &quot;&quot;) + ((($aggrName == &quot;&quot;) &amp;&amp; ($clusName !=
    &quot;&quot;) &amp;&amp; ($vserverName != &quot;&quot;)) ?
    volume1.vfiler.ip_address : &quot;&quot;) +
    ((($aggrName == &quot;&quot;) &amp;&amp; ($clusName == &quot;&quot;)
    &amp;&amp; ($vserverName == &quot;&quot;)) ? volume2.vfiler.ip_address :
    &quot;&quot;) + ((($aggrName != &quot;&quot;) &amp;&amp; ($clusName ==
    &quot;&quot;) &amp;&amp; ($vserverName == &quot;&quot;)) ?
    volume3.vfiler.ip_address : &quot;&quot;) + ((($aggrName != &quot;&quot;)
    &amp;&amp; ($clusName != &quot;&quot;) &amp;&amp; ($vserverName ==
    &quot;&quot;)) ? volume4.vfiler.ip_address : &quot;&quot;) +
    ((($aggrName == &quot;&quot;) &amp;&amp; ($clusName != &quot;&quot;)
    &amp;&amp; ($vserverName == &quot;&quot;)) ? volume5.vfiler.ip_address :
    &quot;&quot;) + &quot;:/vol/&quot; + $volName</value><description>
    </description></returnParameter></returnParameters><atom:link rel='export'
    href='http://192.168.231.200/rest/dars/ea1a0d89-ab4e-4373-846d-bf4541efb1eb'
    /><atom:link rel='self' href='http://192.168.231.200/rest/workflows/ea1a0d8
    9-ab4e-4373-846d-bf4541efb1eb'/><atom:link rel='execute'
    href='http://192.168.231.200/rest/workflows/
    ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs'/><atom:link rel='out-parameter'
    href='http://192.168.231.200/rest/workflows/
    ea1a0d89-ab4e-4373-846d-bf4541efb1eb/out'/><atom:link rel='preview'
    href='http://192.168.231.200/rest/workflows/
    ea1a0d89-ab4e-4373-846d-bf4541efb1eb/preview'/><atom:link
    rel='list' href='http://192.168.231.200/rest/workflows'/></workflow>
    <jobStatus><jobStatus>SCHEDULED</jobStatus><jobType>Workflow Execution -
    os_create_nfs_share_7m</jobType><scheduleType>Immediate</scheduleType>
    <plannedExecutionTime>Feb 1, 2016 3:10:46 PM</plannedExecutionTime>
    <comment>Creation of share from manila service</comment><phase>
    PENDING_PLANNING</phase><userInputValues><userInputEntry key='$protocol'
    value='NFS'/><userInputEntry key='$aggrName' value=''/><userInputEntry
    key='$vserverName' value=''/><userInputEntry key='$clusName' value=''/>
    <userInputEntry key='$volSize' value='1'/><userInputEntry key='$snapSched'
    value='0 0 0'/><userInputEntry key='$volName'
    value='manila_26e05889_c994_46a4_89c1_d50dc5f66238'/><userInputEntry
    key='$deDupe' value=''/></userInputValues><returnParameters/></jobStatus>
    <atom:link rel='out' href='http://192.168.231.200/rest/workflows/
    ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/plan/out'/>
    <atom:link rel='reservation' href='http://192.168.231.200/rest/workflows/
    ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/reservation'/>
    <atom:link rel='self' href='http://192.168.231.200/rest/workflows/
    ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909'/><atom:link rel='add'
    href='http://192.168.231.200/rest/workflows/
    ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs'/><atom:link rel='cancel'
    href='http://192.168.231.200/rest/workflows/
    ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/cancel'/><atom:link
    rel='resume' href='http://192.168.231.200/rest/workflows/
    ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/resume'/>
    <atom:link rel='command-execution-arguments'
    href='http://192.168.231.200/rest/workflows/executions/909'/></job>
    """,
        """<job xmlns:atom='http://www.w3.org/2005/Atom' jobId='909'>
<workflow uuid='ea1a0d89-ab4e-4373-846d-bf4541efb1eb'><name>
os_create_nfs_share_7m</name><description>Creates a volume and exports it over
 NFS. This workflow includes: - Creating a volume with the given name and size.
The volume is created on a suitable aggregate found in the environment. -
Exporting the newly created volume over NFS and granting the specified
privileges to the specified set of hosts.</description><certification>NONE
</certification><version><major>1 </major><minor>0</minor><revision>12
</revision></version><categories> <category>OS Workflows</category>
</categories><userInputList><userInput> <name>clusName</name><type>String
</type><mandatory>false</mandatory></userInput><userInput><name>vserverName
</name><type>String</type><mandatory>false</mandatory></userInput><userInput>
<name>aggrName</name> <type>String</type><mandatory>false</mandatory>
</userInput><userInput><name>protocol</name><defaultValue>nfs</defaultValue>
<type>Enum</type><mandatory>true</mandatory></userInput><userInput>
<name>volName</name><type>String</type><mandatory>true</mandatory>
</userInput><userInput><name>volSize</name><defaultValue></defaultValue>
<type>Number</type><mandatory>true</mandatory></userInput><userInput>
<name>deDupe</name><type>String</type><mandatory>false</mandatory>
</userInput><userInput><name>snapSched</name><defaultValue>'0 0 0'
</defaultValue><type>String</type><mandatory>false</mandatory></userInput>
</userInputList><returnParameters><returnParameter><name>export_location
</name><value> ((($aggrName != &quot;&quot;) &amp;&amp;
($clusName != &quot;&quot;) &amp;&amp; ($vserverName != &quot;&quot;)) ?
volume.vfiler.ip_address : &quot;&quot;) + ((($aggrName == &quot;&quot;)
&amp;&amp; ($clusName != &quot;&quot;) &amp;&amp;
($vserverName != &quot;&quot;)) ? volume1.vfiler.ip_address : &quot;&quot;) +
((($aggrName == &quot;&quot;) &amp;&amp; ($clusName == &quot;&quot;)
&amp;&amp; ($vserverName == &quot;&quot;)) ? volume2.vfiler.ip_address :
&quot;&quot;) + ((($aggrName != &quot;&quot;) &amp;&amp;
($clusName == &quot;&quot;) &amp;&amp; ($vserverName == &quot;&quot;)) ?
volume3.vfiler.ip_address : &quot;&quot;) + ((($aggrName != &quot;&quot;)
&amp;&amp; ($clusName != &quot;&quot;) &amp;&amp; ($vserverName ==
&quot;&quot;)) ? volume4.vfiler.ip_address : &quot;&quot;) +
((($aggrName == &quot;&quot;) &amp;&amp; ($clusName != &quot;&quot;)
&amp;&amp; ($vserverName == &quot;&quot;)) ? volume5.vfiler.ip_address :
&quot;&quot;) + &quot;:/vol/&quot; + $volName</value><description>
</description> </returnParameter></returnParameters><atom:link
rel='export' href='http://192.168.231.200/
rest/dars/ea1a0d89-ab4e-4373-846d-bf4541efb1eb'/>
<atom:link rel='self' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb'/>
<atom:link rel='execute' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs'/>
<atom:link rel='out-parameter' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/out'/>
<atom:link rel='preview' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/preview'/>
<atom:link rel='list' href= 'http://192.168.231.200/rest/workflows'/>
</workflow><jobStatus><jobStatus>SCHEDULED</jobStatus>
<jobType>Workflow Execution - os_create_nfs_share_7m </jobType>
<scheduleType>Immediate</scheduleType>
<plannedExecutionTime>Feb 1, 2016 3:10:46 PM</plannedExecutionTime>
<comment>Creation of share from manila service</comment>
<phase>PENDING_PLANNING</phase><userInputValues>
<userInputEntry key='$protocol' value='NFS'/><userInputEntry
key='$aggrName' value=''/><userInputEntry key='$vserverName' value=''/>
<userInputEntry key='$volSize' value='1'/><userInputEntry key='$clusName'
value=''/><userInputEntry key='$volName'
value='manila_26e05889_c994_46a4_89c1_d50dc5f66238'/>
<userInputEntry key='$snapSched' value='0 0 0'/>
<userInputEntry key='$deDupe' value=''/></userInputValues><returnParameters/>
</jobStatus><atom:link rel='out' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/plan/out'/>
<atom:link rel='reservation' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/reservation'/>
<atom:link rel='self' href='http://192.168.231.200/rest/
workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909'/><atom:link
rel='add' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs'/>
<atom:link rel='cancel' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/cancel'/>
<atom:link rel='resume' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/resume'/>
<atom:link rel='command-execution-arguments' href='http://192.168.231.200/
rest/workflows/executions/909'/></job>
""",
        """<job xmlns:atom='http://www.w3.org/2005/Atom' jobId='909'>
<workflow uuid='ea1a0d89-ab4e-4373-846d-bf4541efb1eb'>
<name>os_create_nfs_share_7m</name><description>Creates a volume and exports
it over NFS. This workflow includes: - Creating a volume with the given name
and size. The volume is created on a suitable aggregate found in the
environment. - Exporting the newly created volume over NFS and granting the
specified privileges to the specified set of hosts.</description>
<certification>NONE</certification><version><major>1</major><minor>0</minor>
<revision>12</revision></version><categories><category>OS Workflows</category>
</categories><userInputList><userInput><name>clusName</name><type>String</type>
<mandatory>false</mandatory></userInput><userInput><name>vserverName</name>
<type>String</type><mandatory>false</mandatory></userInput><userInput>
<name>aggrName</name><type>String</type><mandatory>false</mandatory>
</userInput><userInput><name>protocol</name><defaultValue>nfs</defaultValue>
<type>Enum</type><mandatory>true</mandatory></userInput><userInput>
<name>volName</name><type>String</type><mandatory>true</mandatory></userInput>
<userInput><name>volSize</name><defaultValue></defaultValue><type>Number
</type><mandatory>true</mandatory></userInput><userInput><name>deDupe</name>
<type>String</type><mandatory>false</mandatory></userInput><userInput>
<name>snapSched</name><defaultValue>'0 0 0'</defaultValue><type>String</type>
<mandatory>false</mandatory></userInput></userInputList><returnParameters>
<returnParameter><name>export_location</name><value>
((($aggrName != &quot;&quot;) &amp;&amp; ($clusName != &quot;&quot;)
&amp;&amp; ($vserverName != &quot;&quot;)) ? volume.vfiler.ip_address :
&quot;&quot;) + ((($aggrName == &quot;&quot;) &amp;&amp; ($clusName !=
&quot;&quot;) &amp;&amp; ($vserverName != &quot;&quot;)) ?
volume1.vfiler.ip_address : &quot;&quot;) + ((($aggrName == &quot;&quot;)
&amp;&amp; ($clusName == &quot;&quot;) &amp;&amp; ($vserverName ==
&quot;&quot;)) ? volume2.vfiler.ip_address : &quot;&quot;) +
((($aggrName != &quot;&quot;) &amp;&amp; ($clusName == &quot;&quot;)
&amp;&amp; ($vserverName == &quot;&quot;)) ? volume3.vfiler.ip_address :
&quot;&quot;) + ((($aggrName != &quot;&quot;) &amp;&amp; ($clusName !=
&quot;&quot;) &amp;&amp; ($vserverName == &quot;&quot;)) ?
volume4.vfiler.ip_address : &quot;&quot;) + ((($aggrName == &quot;&quot;)
&amp;&amp; ($clusName != &quot;&quot;) &amp;&amp;
($vserverName == &quot;&quot;)) ? volume5.vfiler.ip_address : &quot;&quot;) +
&quot;:/vol/&quot; + $volName</value><description></description>
</returnParameter></returnParameters><atom:link rel='export'
href='http://192.168.231.200/rest/dars/ea1a0d89-ab4e-4373-846d-bf4541efb1eb'/>
<atom:link rel='self' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb'/>
<atom:link rel='execute' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs'/>
<atom:link rel='out-parameter' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/out'/>
<atom:link rel='preview' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/preview'/>
<atom:link rel='list' href='http://192.168.231.200/rest/workflows'/>
</workflow><jobStatus><jobStatus>COMPLETED</jobStatus>
<jobType>Workflow Execution - os_create_nfs_share_7m</jobType>
<scheduleType>Immediate</scheduleType><startTime>Feb 1, 2016 3:10:51 PM
</startTime><endTime>Feb 1, 2016 3:11:01 PM</endTime>
<plannedExecutionTime>Feb 1, 2016 3:10:46 PM</plannedExecutionTime>
<comment>Creation of share from manila service</comment><phase>EXECUTION
</phase><userInputValues><userInputEntry key='$protocol' value='NFS'/>
<userInputEntry key='$aggrName' value=''/>
<userInputEntry key='$vserverName' value=''/>
<userInputEntry key='$volSize' value='1'/>
<userInputEntry key='$clusName' value=''/>
<userInputEntry key='$volName'
value='manila_26e05889_c994_46a4_89c1_d50dc5f66238'/>
<userInputEntry key='$snapSched' value='0 0 0'/>
<userInputEntry key='$deDupe' value=''/></userInputValues><returnParameters>
<returnParameters key='export_location'
value='192.168.231.51:/vol/manila_26e05889_c994_46a4_89c1_d50dc5f66238'/>
</returnParameters><workflow-execution-progress>
<current-command>Create empty export rule</current-command>
<current-command-index>3</current-command-index><commands-number>3
</commands-number></workflow-execution-progress></jobStatus>
<atom:link rel='out' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/plan/out'/>
<atom:link rel='reservation' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/reservation'/>
<atom:link rel='self' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909'/>
<atom:link rel='add' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs'/>
<atom:link rel='cancel' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/cancel'/>
<atom:link rel='resume' href='http://192.168.231.200/
rest/workflows/ea1a0d89-ab4e-4373-846d-bf4541efb1eb/jobs/909/resume'/>
<atom:link rel='command-execution-arguments' href='http://192.168.231.200/
rest/workflows/executions/909'/></job>
""",
    ],
}

DELETE_SHARE_WORKFLOW = {
    'request_inputs': {
        const.VOLUME_NAME: "test_1234_1234_1234_1234",
    },
    'send_request_calls': [
        mock.call('workflows/f07d9097-1055-4a82-8326-822204f64111/jobs/',
                  mock.ANY),
        mock.call('workflows/f07d9097-1055-4a82-8326-822204f64111/jobs/935'),
    ],
    'responses': [
        """<job xmlns:atom="http://www.w3.org/2005/Atom" jobId="935">
<workflow uuid="f07d9097-1055-4a82-8326-822204f64111">
<name>os_delete_nfs_share_7m</name>
<certification>NONE</certification><version><major>1</major><minor>0</minor>
<revision>0</revision></version><categories><category>OS Workflows</category>
</categories><userInputList><userInput><name>volName</name><type>String</type>
<allowedValues/><mandatory>false</mandatory></userInput></userInputList>
<returnParameters/></workflow><jobStatus><jobStatus>SCHEDULED</jobStatus>
<jobType>Workflow Execution - os_delete_nfs_share_7m</jobType>
<scheduleType>Immediate</scheduleType><plannedExecutionTime>
Feb 2, 2016 2:22:47 PM</plannedExecutionTime><comment>
Deletion of share from manila service</comment><phase>PENDING_PLANNING
</phase><userInputValues><userInputEntry key="$volName"
value="manila_26e05889_c994_46a4_89c1_d50dc5f66238"/></userInputValues>
<returnParameters/></jobStatus></job>
""",
        """<job xmlns:atom="http://www.w3.org/2005/Atom" jobId="935">
<workflow uuid="f07d9097-1055-4a82-8326-822204f64111">
<name>os_delete_nfs_share_7m</name>
<certification>NONE</certification><version><major>1</major><minor>0</minor>
<revision>0</revision></version><categories><category>OS Workflows</category>
</categories><userInputList><userInput><name>volName</name><type>String</type>
<mandatory>false</mandatory></userInput></userInputList><returnParameters/>
<atom:link rel="export" href="http://192.168.231.200/
rest/dars/f07d9097-1055-4a82-8326-822204f64111"/><atom:link rel="self"
href="http://192.168.231.200/
rest/workflows/f07d9097-1055-4a82-8326-822204f64111"/><atom:link rel="execute"
href="http://192.168.231.200/
rest/workflows/f07d9097-1055-4a82-8326-822204f64111/jobs"/><atom:link
rel="out-parameter" href="http://192.168.231.200/
rest/workflows/f07d9097-1055-4a82-8326-822204f64111/out"/><atom:link
rel="preview" href="http://192.168.231.200/
rest/workflows/f07d9097-1055-4a82-8326-822204f64111/preview"/><atom:link
rel="list" href="http://192.168.231.200/rest/workflows"/></workflow>
<jobStatus><jobStatus>COMPLETED</jobStatus><jobType>Workflow Execution
- os_delete_nfs_share_7m</jobType><scheduleType>Immediate</scheduleType>
<startTime>Feb 2, 2016 2:22:51 PM</startTime><endTime>Feb 2, 2016 2:23:00 PM
</endTime><plannedExecutionTime>Feb 2, 2016 2:22:47 PM</plannedExecutionTime>
<comment>Deletion of share from manila service</comment><phase>EXECUTION
</phase><userInputValues><userInputEntry key="$volName"
value="manila_26e05889_c994_46a4_89c1_d50dc5f66238"/></userInputValues>
<returnParameters/><workflow-execution-progress><current-command>Execute
Update of WFA Datasource</current-command><current-command-index>4
</current-command-index><commands-number>4</commands-number>
</workflow-execution-progress></jobStatus><atom:link rel="out"
href="http://192.168.231.200/
rest/workflows/f07d9097-1055-4a82-8326-822204f64111/jobs/935/plan/out"/>
<atom:link rel="reservation" href="http://192.168.231.200/
rest/workflows/f07d9097-1055-4a82-8326-822204f64111/jobs/935/reservation"/>
<atom:link rel="self" href="http://192.168.231.200/
rest/workflows/f07d9097-1055-4a82-8326-822204f64111/jobs/935"/><atom:link
rel="add" href="http://192.168.231.200/
rest/workflows/f07d9097-1055-4a82-8326-822204f64111/jobs"/><atom:link
rel="cancel" href="http://192.168.231.200/rest/workflows/
f07d9097-1055-4a82-8326-822204f64111/jobs/935/cancel"/><atom:link rel=
"resume" href="http://192.168.231.200/
rest/workflows/f07d9097-1055-4a82-8326-822204f64111/jobs/935/
resume"/><atom:link rel="command-execution-arguments"
href="http://192.168.231.200/rest/workflows/executions/935"/></job>"""
    ],
}

CREATE_SNAPSHOT_WORKFLOW = {
    'request_inputs': {
        const.VOLUME_NAME: 'test_5678_5678_5678_5678',
        const.SNAPSHOT_NAME: 'snap_9999_9999_9999_9999',
    },
    'send_request_calls': [
        mock.call('workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/',
                  mock.ANY),
        mock.call('workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940'),
    ],
    'responses': [
        """<job xmlns:atom="http://www.w3.org/2005/Atom" jobId="940">
<workflow uuid="096d4f1d-aad0-4e23-973d-4302a0d2b8ad">
<name>os_create_snapshot_7m</name>
<certification>NONE</certification><version><major>1</major><minor>0</minor>
<revision>1</revision></version><categories><category>OS Workflows</category>
</categories><userInputList><userInput><name>snapName</name><type>String</type>
<allowedValues/><mandatory>false</mandatory></userInput><userInput><name>
volName</name><type>String</type><allowedValues/><mandatory>false</mandatory>
</userInput></userInputList><returnParameters/><atom:link rel="export"
href="http://192.168.231.200/rest/dars/096d4f1d-aad0-4e23-973d-4302a0d2b8ad"/>
<atom:link rel="self" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad"/><atom:link rel="execute"
href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs"/><atom:link
rel="out-parameter" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/out"/>
<atom:link rel="preview" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/preview"/><atom:link
rel="list" href="http://192.168.231.200/rest/workflows"/></workflow>
<jobStatus><jobStatus>SCHEDULED</jobStatus><jobType>Workflow Execution
- os_create_snapshot_7m</jobType><scheduleType>Immediate</scheduleType>
<plannedExecutionTime>Feb 2, 2016 3:17:41 PM</plannedExecutionTime>
<comment>Creation of snapshot from share over manila service</comment>
<phase>PENDING_PLANNING</phase><userInputValues><userInputEntry
key="$snapName" value="manila_45f486d5_2a23_4a18_8a1d_d0ecbf70b0a8_snapshot"/>
<userInputEntry key="$volName"
value="manila_d187b5a0_14e6_4e7a_b8db_3784539b23c5"/></userInputValues>
<returnParameters/></jobStatus><atom:link rel="out"
href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940/plan/out"/>
<atom:link rel="reservation" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940/reservation"/>
<atom:link rel="self" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940"/><atom:link
rel="add" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs"/><atom:link
rel="cancel" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940/cancel"/>
<atom:link rel="resume" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940/resume"/>
<atom:link rel="command-execution-arguments" href="http://192.168.231.200/
rest/workflows/executions/940"/></job>
""",
        """<job xmlns:atom="http://www.w3.org/2005/Atom" jobId="940">
<workflow uuid="096d4f1d-aad0-4e23-973d-4302a0d2b8ad">
<name>os_create_snapshot_7m</name>
<certification>NONE</certification><version><major>1</major><minor>0</minor>
<revision>1</revision></version><categories><category>OS Workflows</category>
</categories><userInputList><userInput><name>snapName</name><type>String
</type><mandatory>false</mandatory></userInput><userInput><name>volName</name>
<type>String</type><mandatory>false</mandatory></userInput></userInputList>
<returnParameters/><atom:link rel="export" href="http://192.168.231.200/
rest/dars/096d4f1d-aad0-4e23-973d-4302a0d2b8ad"/><atom:link rel="self"
href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad"/><atom:link rel="execute"
href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs"/><atom:link
rel="out-parameter" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/out"/><atom:link
rel="preview" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/preview"/><atom:link
rel="list" href="http://192.168.231.200/rest/workflows"/></workflow>
<jobStatus><jobStatus>COMPLETED</jobStatus><jobType>Workflow Execution
- os_create_snapshot_7m</jobType><scheduleType>Immediate</scheduleType>
<startTime>Feb 2, 2016 3:17:45 PM</startTime><endTime>Feb 2, 2016 3:17:50 PM
</endTime><plannedExecutionTime>Feb 2, 2016 3:17:41 PM</plannedExecutionTime>
<comment>Creation of snapshot from share over manila service</comment>
<phase>EXECUTION</phase><userInputValues><userInputEntry key="$snapName"
value="manila_45f486d5_2a23_4a18_8a1d_d0ecbf70b0a8_snapshot"/><userInputEntry
key="$volName" value="manila_d187b5a0_14e6_4e7a_b8db_3784539b23c5"/>
</userInputValues><returnParameters/><workflow-execution-progress>
<current-command>Execute Update of WFA Datasource</current-command>
<current-command-index>3</current-command-index><commands-number>3
</commands-number></workflow-execution-progress></jobStatus><atom:link
rel="out" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940/plan/out"/>
<atom:link rel="reservation" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940/reservation"/>
<atom:link rel="self" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940"/><atom:link
rel="add" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs"/><atom:link
rel="cancel" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940/cancel"/>
<atom:link rel="resume" href="http://192.168.231.200/
rest/workflows/096d4f1d-aad0-4e23-973d-4302a0d2b8ad/jobs/940/resume"/>
<atom:link rel="command-execution-arguments" href="http://192.168.231.200/
rest/workflows/executions/940"/></job>
""",
    ]
}

DELETE_SNAPSHOT_WORKFLOW = {
    'request_inputs': {
        const.SNAPSHOT_NAME: 'snap_9999_9999_9999_9999',
    },
    'send_request_calls': [
        mock.call('workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/',
                  mock.ANY),
        mock.call('workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943'),
    ],
    'responses': [
        """<job xmlns:atom="http://www.w3.org/2005/Atom" jobId="943">
<workflow uuid="e25e0c9c-2c64-434a-8f00-e0d24f306df6">
<name>os_delete_snapshot_7m</name>
<certification>NONE</certification><version><major>1</major><minor>0</minor>
<revision>1</revision></version><categories><category>OS Workflows</category>
</categories><userInputList><userInput><name>snapName</name><type>String
</type><allowedValues/><mandatory>false</mandatory></userInput>
</userInputList><returnParameters/><atom:link rel="export" href=
"http://192.168.231.200/rest/dars/e25e0c9c-2c64-434a-8f00-e0d24f306df6"/>
<atom:link rel="self" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6"/><atom:link rel="execute"
href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs"/><atom:link
rel="out-parameter" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/out"/><atom:link
rel="preview" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/preview"/><atom:link
rel="list" href="http://192.168.231.200/rest/workflows"/></workflow>
<jobStatus><jobStatus>SCHEDULED</jobStatus><jobType>Workflow Execution
- os_delete_snapshot_7m</jobType><scheduleType>Immediate</scheduleType>
<plannedExecutionTime>Feb 2, 2016 3:57:16 PM</plannedExecutionTime>
<comment>Deletion of snapshot over manila service</comment>
<phase>PENDING_PLANNING</phase><userInputValues><userInputEntry
key="$snapName"
value="manila_45f486d5_2a23_4a18_8a1d_d0ecbf70b0a8_snapshot"/>
</userInputValues><returnParameters/></jobStatus><atom:link rel="out"
href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943/plan/out"/>
<atom:link rel="reservation" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943/reservation"/>
<atom:link rel="self" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943"/><atom:link
rel="add" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs"/><atom:link
rel="cancel" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943/cancel"/>
<atom:link rel="resume" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943/resume"/>
<atom:link rel="command-execution-arguments" href="http://192.168.231.200/
rest/workflows/executions/943"/></job>
""",
        """<job xmlns:atom="http://www.w3.org/2005/Atom" jobId="943">
<workflow uuid="e25e0c9c-2c64-434a-8f00-e0d24f306df6">
<name>os_delete_snapshot_7m</name>
<certification>NONE</certification><version><major>1</major><minor>0</minor>
<revision>1</revision></version><categories><category>OS Workflows</category>
</categories><userInputList><userInput><name>snapName</name><type>String
</type><mandatory>false</mandatory></userInput></userInputList>
<returnParameters/><atom:link rel="export" href="http://192.168.231.200/
rest/dars/e25e0c9c-2c64-434a-8f00-e0d24f306df6"/><atom:link rel="self"
href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6"/><atom:link rel="execute"
href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs"/><atom:link
rel="out-parameter" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/out"/><atom:link
rel="preview" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/preview"/><atom:link
rel="list" href="http://192.168.231.200/
rest/workflows"/></workflow><jobStatus><jobStatus>COMPLETED</jobStatus>
<jobType>Workflow Execution - os_delete_snapshot_7m</jobType>
<scheduleType>Immediate</scheduleType><startTime>Feb 2, 2016 3:57:21 PM
</startTime><endTime>Feb 2, 2016 3:57:25 PM</endTime>
<plannedExecutionTime>Feb 2, 2016 3:57:16 PM</plannedExecutionTime>
<comment>Deletion of snapshot over manila service</comment><phase>EXECUTION
</phase><userInputValues><userInputEntry key="$snapName"
value="manila_45f486d5_2a23_4a18_8a1d_d0ecbf70b0a8_snapshot"/>
</userInputValues><returnParameters/><workflow-execution-progress>
<current-command>Execute Update of WFA Datasource</current-command>
<current-command-index>3</current-command-index><commands-number>3
</commands-number></workflow-execution-progress></jobStatus><atom:link
rel="out" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943/plan/out"/>
<atom:link rel="reservation" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943/reservation"/>
<atom:link rel="self" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943"/><atom:link
rel="add" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs"/>
<atom:link rel="cancel" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943/cancel"/>
<atom:link rel="resume" href="http://192.168.231.200/
rest/workflows/e25e0c9c-2c64-434a-8f00-e0d24f306df6/jobs/943/resume"/>
<atom:link rel="command-execution-arguments" href="http://192.168.231.200/
rest/workflows/executions/943"/></job>
""",
    ],
}
