serviceAmiIdChanged = [: ] // to store the serviceName: amiIsChangedOrNot
String cron_string = "0 0 */20 * *" // cron every 20th of the month

/*
  @purpose: utility function to send an email
  @params: subject: String
           body: String
           recipients: string separated by commas 
 */ 
def sendEmail(subject, body, recipients) {

  emailext body: "${body}",
  to: "${recipients}",
    subject: "${subject}"
}

/*
  @purpose:  utility function to create a stage
  @params: stageName: String
           jobName: String
 */ 
def createStage(stageName, jobName) {

  script {

    // if the ami is changed then only build the service specific job.
    if (serviceAmiIdChanged["${jobName}"] == "True") {

      try {

        stage("${stageName}") {

          build job: "${jobName}"

        }

        // sendEmail("", "", "")
        // slackSend(channel: "#channelName", message: "Message")
      } catch (Exception e) {

        println(e.getMessage());
        // sendEmail("", "", "")
        // slackSend(channel: "#channelName", message: "Message")


        throw e;

      }
    }

  }

}

// actual pipeline 
pipeline {
  agent none
  // trigers at the expression specified in cron 
  // triggers {
  //   cron(cron_string)
  // }
  // parameter for the pipeline
  parameters {
    string(name: 'AWS_AGENT_LABEL', defaultValue: 'any', description: 'Label of the Agent which has python3 and aws profile configured')
    string(name: 'AWS_SERVICE_CONFIG_FILE', defaultValue: './config/config.json', description: 'Path of the aws service config file')
  }

  // stages start from here
  stages {
    //  check for the ami version and if the ami is different , then go to the next stage.
    stage('check the ami version') {

      agent { label "${AWS_AGENT_LABEL}"}
      steps {

        // stash to be used in jira automation
        stash includes: '**', name: 'jiraSource'

        script {

          // run the script to determine whether the ami is changed or not
          def result = sh(returnStdout: true, script: 'python3 check_ami_version.py')
          // example output: {FirstServiceName:True,SecondServiceName:False}
          //  True means, the ami used in launch configuration is different from the latest created ami.
          for (String jobStatus: result.split(',')) {

            String[] eachjobStatus = jobStatus.split(':');

            if (eachjobStatus.size() > 1) {

              serviceAmiIdChanged[eachjobStatus[0]] = eachjobStatus[1];
            }

          }
        }
      }
    }

    // create the jobs dynamically
    stage("QA") {

      steps {

        // createStage("kodak", "")
        // createStage("content-origin", "")
        // createStage("Dreamcatcher", "")
        // createStage("Concierge", "")
        // createStage("MUS", "")
        // createStage("VMS", "")
        echo "hello world"

      }

    }
  }
  post {
    always {
      echo "====++++always++++===="
    }
    // if its a success,then create a  jira ticket for the UAT approval.
    success {
      echo "====++++only when successful ++++===="
      node("${AWS_AGENT_LABEL}") {
        withCredentials([
          [
            $class: 'UsernamePasswordMultiBinding',
            credentialsId: "jira-cred",
            usernameVariable: 'JIRA_USERNAME',
            passwordVariable: 'JIRA_API_TOKEN',
          ]
        ]) {
          
          // if there is any change in ami then only create ticket , otherwise dont.
          script{
            if(serviceAmiIdChanged.size() > 0) {

                // unstash the jira module 
                unstash "jiraSource"
                // create the jira ticket
                ticketNumber = sh(returnStdout: true, script: 'python3 scripts/create_issue.py')
                // remove any extra new line character.
                ticketNumber = ticketNumber.replaceAll("[\n\r]", "");
                // build the second pipeline to provide the ticket Number as an argument 
            }
          }
        }

      }
    }
    failure {
      echo "====++++only when failed++++===="
    }
  }

}