//  store 'region': 'latest ami is present or not'
def serviceAmiIdChanged = [: ]
String cron_string = "0 0 */20 * *" // cron every 20th of the month

pipeline {
  agent none
  triggers {
    cron(cron_string)
  }
  parameters {

    string(name: 'AWS_AGENT_LABEL', defaultValue: 'any', description: 'Label of the Agent which has python3 and aws profile configured')
    string(name: 'AWS_SERVICE_CONFIG_FILE', defaultValue: './config/config.json', description: 'Path of the aws service config file')
    string(name: 'JOB_NAMES', description: 'List of jobs separated by commas in build sequence (job names for the service).')
  }

  stages {
    stage('check the ami version') {
      agent any
      steps {
        withCredentials([
          [
            $class: 'AmazonWebServicesCredentialsBinding',
            credentialsId: "aws-creds",
            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
          ]
        ]) {
            
           stash includes: 'jira/*', name: 'jiraSource'
           stash includes: 'scripts/*', name: 'jiraScript'
          script {
            
            def result = sh(returnStdout: true, script: 'python3 check_ami_version.py')
            println(result);
           
            for (String jobStatus: result.split(',')) {

              String[] eachjobStatus = jobStatus.split(':');

              if (eachjobStatus.size() > 1) {

                serviceAmiIdChanged[eachjobStatus[0]] = eachjobStatus[1];
              }

            }
          }
        }
      }
    }
    // create the jobs dynamically
    stage('build the QA services if the latest ami id is present') {

      steps {

        script {

          String[] jobList = params.JOB_NAMES.split(',');

          if (jobList.size() > 0) {

            for (String eachJob: jobList) {

              if (serviceAmiIdChanged["${eachJob}"] == 'False') {

                try {
                    
                    stage("${eachJob}"){
                      
                      build job: "${eachJob}"
                    
                    }

                    // emailext body: "${eachJob} succeeded", recipientProviders: [buildUser()], subject: "JOB ${eachJob} SUCCESS", to: 'ragaws1674@gmail.com'
                } catch (Exception e) {

                  println(e.getMessage());
                  // emailext body: "${eachJob} failed", recipientProviders: [buildUser()], subject: "JOB ${eachJob} FAILED", to: 'ragaws1674@gmail.com'
                  throw e;

                }

              }
            
            }

          }

        }
      }
    }
  }
  post {
    always {
      echo "====++++always++++===="
    }
    success {
      echo "====++++only when successful ++++===="
      node("${AWS_AGENT_LABEL}"){
        withCredentials([[
            $class: 'UsernamePasswordMultiBinding',
            credentialsId: "jira-cred",
            usernameVariable: 'JIRA_USERNAME',
            passwordVariable: 'JIRA_API_TOKEN',
        ]]) {
            
            unstash "jiraSource"
            unstash "jiraScript"
            sh """
              ls -l
              export JIRA_USERNAME="${JIRA_USERNAME}"
              export JIRA_API_TOKEN="${JIRA_API_TOKEN}"
              python3 scripts/create_issue.py
              """
        }

      }
    }
    failure {
      echo "====++++only when failed++++===="
    }
  }

}