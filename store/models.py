from dataclasses import dataclass, field
from enum import Enum
from typing import Any,OrderedDict as OrderedDictType

class INSTANCE_REFRESH_STATUS(Enum):
    SUCCESS = 'Successful'
    IN_PROGRESS = 'InProgress'
    PENDING = 'Pending'
    NOT_STARTED = 'NotStarted'

@dataclass
class RegionState:
    region_name: str = ''
    latest_ami_id: str = ''
    launch_config_ami_id: str = ''
    launch_config: dict[str,Any] = field(default_factory=dict)
    asg_name: str = ''
    instance_refresh_config: dict[str,str] = field(default_factory=dict)
    ami_changed: bool = False 
    refresh_status: INSTANCE_REFRESH_STATUS = INSTANCE_REFRESH_STATUS.NOT_STARTED.value

@dataclass
class ServiceState:
    region_states: dict[str,RegionState] = field(default_factory=dict)


@dataclass
class AppState:
    state: OrderedDictType[str,ServiceState] = field(default_factory=OrderedDictType)
    
    