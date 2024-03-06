BIG-IP配置补齐和NG Auditor 需求分析
 
**主要输入：**


1.	Auditor 会以命令行的方式运行
2.	Auditor 会抓取 Neutron DB，DB 建立连接需要的信息，通过命令行提供 /etc/neutron/neutron.conf 配置文件寻找 connection 配置。
3.	Auditor 会抓取 Bigip 上数据，Bigip 连接需要的加密 username，password。通过 Neutron DB 中 lbaas_loadbalanceragentbindings, lbaas_devices 和 lbaas_device_members  中信息定位，如果 management IP 存在双栈，初步版本只支持 IPv4 management IP。
4.	Auditor 产生 Bash script 需要 keystone admin 角色调用lbaas rebuild 命令，admin rc 文件需要通过命令行提供。

**检查有无的配置粒度包含以下资源（针对单机不在线，创建删除资源双机不一致状况）：**


tenant（partition）， loadbalancer （vip），snatpool（pool 级别），selfip，vlan，route domain，route（gateway），listener（vs），pool，pool member，pool healthmonitor，l7rule (irule)。

**主备 bigip 互比（属性配置）的粒度包含以下资源（针对单机不在线，mutable 可更改资源更新不一致的状况）：**


virtual_address, snatpool, cookie_persistence, universal_persistence, sip_persistence, source_addr_persistence, http_profile, tcp_profile, http2_profile, client_ssl_profile, cipher_group, cipher_rule, bwc_policy, l7policy, http_monitor, https_monitor, tcp_monitor, ping_monitor, pool, member

**运行命令：** 


`f5-agent-auditor --config-file /etc/neutron/neutron.conf --rcfile-path /root/pzhang/pzhang.rc --rebuild --nodebug`

**主要输出：**


1.	审计结果有无和差异资源信息会输出在 /tmp 目录中。
2.	Rebuild Bash 脚本会输出在 /tmp 目录中。
3.	Rebuild Bash 脚本运行 log 会输出在 /tmp 目录中。
4.	Auditor 本身运行可以使用选择输出在屏幕或者文件中。

**Auditor的审计文件记录内容：**


1.	有无： missing 和 unknown 文件。
2.	差异： diff 文件。

**审计文件名称：missing_<bigip-ip>_<timestamp>**


用于记录Bigip 上缺失的 lbaas 配置和其关联的 loadbalancer。
审计文件内容：

```
{
    "<agent-id>": {
        "<project-id>": {
            "<missing-resource-name>": [
                "<missing-resource-related-loadbalancers>",
                "<missing-resource-related-loadbalancers>",
                ...
            ]
        }
}，
	    "<agent-id>": {
        "<project-id>": {
            "<missing-resource-name>": {
                "<missing-resource-related-loadbalancers>",
            }
        }
},
…
}
```
	
**Rebuild all Bash 脚本文件名称：rebuild_all_<timestamp>.sh**


Bash 脚本用于 rebuild loadbalancer。
Rebuild all Bash 脚本文件内容：

```
#!/bin/bash

wait_until_loadbalancer () {
  local LB=$1
  local EXPECTED_STATUS=$2
  local STATUS="unknown"
  local timeout=60

  while [[ $STATUS != $EXPECTED_STATUS ]] && [[ $timeout -gt 0 ]] ; do
    STATUS=$(neutron lbaas-loadbalancer-show $LB | grep provisioning_status | awk '{ print $4 }')
    if [[ $STATUS == "ERROR" ]] ; then
      echo "$(date): $LB is in $STATUS state."
      return 1
    fi
    if [[ $STATUS != $EXPECTED_STATUS ]] ; then
      sleep 1
      ((timeout=timeout-1))
    else
      echo "$(date): $LB is in $STATUS state"
      break
    fi
  done

  if [[ $timeout -lt 0 ]]; then
      echo "$(date): $LB rebuild checking timeout"
  fi
}

source /root/pzhang/pzhang.rc

logfile=/tmp/rebuild_$(date +%Y%m%d_%H%M%S).log

rm -rf $logfile
touch $logfile




neutron lbaas-loadbalancer-rebuild --all f7183210-25b2-435f-893a-d0ce66069181
wait_until_loadbalancer f7183210-25b2-435f-893a-d0ce66069181 ACTIVE >> $logfile

rebuild all bash 运行后产生的 log 文件名称：rebuild_<timestamp>.log
记录 rebuild bash 脚本执行结果。
rebuild all bash 运行后 log 内容：
Wed Dec 13 14:57:19 CST 2023: 616c92e2-12db-4327-8af7-fb223ade6e31 is in ACTIVE state
Wed Dec 13 14:57:36 CST 2023: 0171629c-2fab-4109-8da8-c65024c7ac24 is in ACTIVE state
Wed Dec 13 14:57:55 CST 2023: dac67cbf-c314-4500-9f81-b1ee4e13392c is in ACTIVE state
Wed Dec 13 14:58:20 CST 2023: b0e33fa5-3625-4140-9733-4b3544a1f543 is in ACTIVE state
…
```

**审计文件名称：unknown_<bigip-ip>_<timestamp>**


记录 Bigip 上多于 lbaas 配置的脏数据。
审计文件内容：

```
{
    "Project_f00e925a7095432ca32ba528f2599b30": {},
    "Project_6fd06a50b7824ae48386565786e94b38": {
        "vlans": [
            "unknown"
        ],
        "gateways": [
            "tes"
        ],
        "rds": [
            "ttt"
        ],
        "selfips": [
            "disselfip"
        ]
    }
}
```

**审计文件名称：diff_<active-bigip-ip>_<backup-bigip-ip>_<timestamp>**


记录备机相对主机不一致的部分。
审计文件内容:

```
{
   "http2_profile": {},
    "http_monitor": {},
    "cipher_rule": {},
    "cookie_persistence": {},
    "l7policy": {},
    "snatpool": {
        "/Common/CORE_56137826-e1de-4e76-a67e-49e49a4cfa6a": {
            "active": {
                "kind": "tm:ltm:snatpool:snatpoolstate",
                "name": "CORE_56137826-e1de-4e76-a67e-49e49a4cfa6a",
                "generation": 1,
                "partition": "Common",
                "members": [
                    "/Common/10.250.19.12%0",
                    "/Common/10.250.19.21%0",
                    "/Common/2005:db8:cafe:16::11%0"
                ],
                "membersReference": [
                    {
                        "link": "https://localhost/mgmt/tm/ltm/snat-translation/~Common~10.250.19.12%250?ver=15.1.10"
                    },
                    {
                        "link": "https://localhost/mgmt/tm/ltm/snat-translation/~Common~10.250.19.21%250?ver=15.1.10"
                    },
                    {
                        "link": "https://localhost/mgmt/tm/ltm/snat-translation/~Common~2005:db8:cafe:16::11%250?ver=15.1.10"
                    }
                ],
                "fullPath": "/Common/CORE_56137826-e1de-4e76-a67e-49e49a4cfa6a",
                "selfLink": "https://localhost/mgmt/tm/ltm/snatpool/~Common~CORE_56137826-e1de-4e76-a67e-49e49a4cfa6a?ver=15.1.10"
            },
            "backup": null
        }
    },
    "virtual_address": {},
    "cipher_group": {},
    "http_profile": {},
    "ping_monitor": {},
    "source_addr_persistence": {},
    "tcp_monitor": {},
    "https_monitor": {},
    "bwc_policy": {},
    "tcp_profile": {},
    "client_ssl_profile": {},
    "sip_persistence": {},
    "pool": {},
    "universal_persistence": {}
    …
}
```

**Auditor使用方式**


命令行：	

`f5-agent-auditor --config-file /etc/neutron/neutron.conf --rcfile-path /root/pzhang/pzhang.rc --rebuild --nodebug`

* --config-file: 指定 neutron.conf 文件，主要是用了里面的 mysql connection配置。

* --rcfile-path：指定admin 角色的 keystone RC 文件。

* --rebuild：指定自动运行 rebuild bash 脚本。如果带此参数，会自动运行auditor 生成的rebuild 脚本。

* --nodebug：命令行运行情况下可以选择不输出部分 debug log。

Rebuild all bash 脚本手工运行/自动运行：


Rebuild bash 脚本可以通过 参数指定自动运行。如果不指定 参数，则需要在 bash 脚本产生后，手动到 /tmp 目录下运行 bash <rebuild_all.sh> 脚本。


**命令行手动/自动运行**：


可以手动运行 f5-agent-auditor 命令，也可以通过配置crontab 自动在某个时间运行f5-agent-auditor 命令。


**执行和权限（包含自动化执行）**


f5-agent-auditor： 需要用 linux root 或者 neutron linux user 级别的角色运行保障文件可执行，/tmp 文件可以读写 log，keystone admin rc file 可读，bash脚本可执行。

Rebuild all bash 脚本：如果手动运行需要 linux root 或者 openstack linux user 级别的角色，可执行 neutron rebuild 命令，可读 keystone admin rc file 和在/tmp 目录下读写权限。

命令行中 refile-path 提供的 rc 配置：需要是 keystone admin 角色，需要可以执行各个 loadbalancer rebuild 级别的命令。  
