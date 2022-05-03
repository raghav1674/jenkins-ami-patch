import dataclasses
from store.models import INSTANCE_REFRESH_STATUS, AppState, RegionState, ServiceState

class AppStateManager:

    def __init__(self):
        self.appState = AppState()

    # init

    def init_service_state(self,service_name):
        self.appState.state[service_name] = ServiceState()

    def init_region_state(self,service_name,region):
        self.appState.state[service_name].region_states[region] = RegionState()
        self.appState.state[service_name].region_states[region].region_name = region

    def __init_empty_state(self,service_name,region):
        if service_name not in self.appState.state:
            self.init_service_state(service_name)
        if region is not None and region not in self.appState.state[service_name].region_states: 
            self.init_region_state(service_name,region)
    # setters 

    def set_region_state(self,service_name,region,region_state):
        self.__init_empty_state(service_name,region)
        self.appState.state[service_name].region_states[region] = region_state

    def set_ami_changed(self,service_name,region):
        self.__init_empty_state(service_name,region)
        self.appState.state[service_name].region_states[region].ami_changed = True 

    def set_latest_ami_id(self,service_name,region,latest_ami_id):
        self.__init_empty_state(service_name,region)
        self.appState.state[service_name].region_states[region].latest_ami_id = latest_ami_id

    def set_latest_lc_ami_id(self,service_name,region,lc_ami_id):
        self.__init_empty_state(service_name,region)
        self.appState.state[service_name].region_states[region].launch_config_ami_id = lc_ami_id

    def set_asg_name(self,service_name,region,asg_name):
        self.__init_empty_state(service_name,region)
        self.appState.state[service_name].region_states[region].asg_name = asg_name

    def set_lc_config(self,service_name,region,lc_config):
        self.__init_empty_state(service_name,region)
        self.appState.state[service_name].region_states[region].launch_config = lc_config
    
    def set_instance_refresh_config(self,service_name,region,refresh_config):
        self.__init_empty_state(service_name,region)
        self.appState.state[service_name].region_states[region].instance_refresh_config = refresh_config

    def set_refresh_status_as_inprogress(self,service_name,region):
        self.__init_empty_state(service_name,region)
        self.appState.state[service_name].region_states[region].refresh_status = INSTANCE_REFRESH_STATUS.IN_PROGRESS.value

    def set_refresh_status_as_success(self,service_name,region):
        self.__init_empty_state(service_name,region)
        self.appState.state[service_name].region_states[region].refresh_status = INSTANCE_REFRESH_STATUS.SUCCESS.value
        
    # getters
    
    def get_latest_ami_id(self,service_name,region):
        return self.appState.state[service_name].region_states[region].latest_ami_id

    def get_latest_lc_ami_id(self,service_name,region):
        return self.appState.state[service_name].region_states[region].launch_config_ami_id

    def get_lc_config(self,service_name,region):
        return self.appState.state[service_name].region_states[region].launch_config
    
    def get_instance_refresh_config(self,service_name,region):
        return self.appState.state[service_name].region_states[region].instance_refresh_config

    def get_service_state(self,service_name):
        return self.appState.state[service_name]

    

    def is__instance_refresh_completed_for_service(self,service_name):
        region_states = self.appState.state[service_name].region_states
        total_count = len(region_states)
        success_refresh_count = 0
        refresh_count = 0
        for region in region_states:
            refresh_status = region_states[region].refresh_status
            if refresh_status == INSTANCE_REFRESH_STATUS.SUCCESS.value:
                success_refresh_count += 1
            if refresh_count != INSTANCE_REFRESH_STATUS.NOT_STARTED.value:
                refresh_count += 1
        return { 'all_refreshed': total_count == refresh_count,
                  'successful_refreshed': total_count == success_refresh_count          
        }  

    def get_service_state_as_dict(self,service_name):
        self.__init_empty_state(service_name,None)
        return dataclasses.asdict(self.appState.state[service_name])

    def get_state_as_dict(self):
        return dataclasses.asdict(self.appState)
    
    def reset(self):
        self.appState = None 

    