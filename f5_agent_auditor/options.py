# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from oslo_config import cfg
import sys

# require f5 agent is installed
from f5_openstack_agent.lbaasv2.drivers.bigip import opts
from f5_openstack_agent.lbaasv2.drivers.bigip import icontrol_driver
from oslo_db import options

tool_opts = [
    cfg.StrOpt("rcfile-path", required=True),
    cfg.BoolOpt("rebuild", default=False),
    cfg.BoolOpt("skip-discon", default=False)
]

cfg.CONF.register_cli_opts(tool_opts)


def load_options(conf=cfg.CONF):
    conf.register_opts(opts.OPTS)
    conf.register_opts(icontrol_driver.OPTS)


def load_db_options(conf=cfg.CONF):
    options.set_defaults(conf)


def parse_options(args=sys.argv[1:],
                  conf=cfg.CONF,
                  project="f5-lbaas-auditor"):
    conf(args, project)


load_db_options()
load_options()
parse_options()
