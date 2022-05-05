import jenkins
import logging
import concurrent.futures

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

class JenkinsApi:

    __shared_jenkins_client = None 

    def __init__(self,jenkins_url,username,api_token):
        if JenkinsApi.__shared_jenkins_client is None:
            JenkinsApi.__shared_jenkins_client = jenkins.Jenkins(jenkins_url, username=username, password=api_token)
        self.__jenkins_client = JenkinsApi.__shared_jenkins_client

    def __print_helper(self,number):
        last_digit = str(number)[-1]
        if last_digit == "1":
            return "st"
        elif last_digit == "2":
            return "nd"
        elif last_digit == "3":
            return "rd"
        return "th"

    def run_job(self,job_name):
        result =  None 
        try:
            next_build_number = self.__jenkins_client.get_job_info(job_name)['nextBuildNumber']
            self.__jenkins_client.build_job(job_name)
            building = True
            while building:
                try:
                    build_info = self.__jenkins_client.get_build_info(job_name, next_build_number)
                    building = build_info['building']
                    result = build_info["result"]
                    build_number = str(build_info["number"]) + self.__print_helper(build_info["number"])
                    logger.info(f'building {job_name} {build_number} time......')
                except jenkins.JenkinsException:
                    logger.warning(f'Unable to find job {job_name} with build number {next_build_number}. Retrying....') 
                except Exception as e:
                    logger.error(f'Some error occurred while building job {job_name}: {e}')
        except jenkins.NotFoundException:
            logger.error(f'No job found with the given name {job_name}')
        except Exception as e:
            logger.error(f'Some error occurred while building job {job_name}: {e}')
        return result

    def run_jobs_in_parallel(self,jobs):
        num_jobs = len(jobs)
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_jobs) as executor:
            futures = [executor.submit(self.run_job, job_name) for job_name in jobs]
        status = []
        for future in concurrent.futures.as_completed(futures):
            status.append(future.result())
        return status

if __name__ == '__main__':
    jenkins_client = JenkinsApi("http://jenkins.com:8080","admin", "213213213")
    print(jenkins_client.run_jobs_in_parallel(["firstTestJob","secondtTestJob"]))