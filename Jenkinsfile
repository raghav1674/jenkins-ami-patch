serviceAmiIdChanged = [: ] // to store the serviceName: amiIsChangedOrNot
String cron_string = "0 0 */20 * *" // cron every 20th of the month

// send the email 
def sendEmail(subject, body, recipients) {

  emailext body: "${body}"
  to: "${recipients}",
    subject: "${subject}"
}

// function to create a stage 
def createStage(stageName, jobName) {

  script {

    if (serviceAmiIdChanged["${jobName}"] == "True") {

      try {

        stage("${stageName}") {

          build job: "${jobName}"

        }

        sendEmail("", "", "")
      } catch (Exception e) {

        println(e.getMessage());
        sendEmail("", "", "")

        throw e;

      }
    }

  }

}

// actual pipeline 
pipeline {
  agent none
  // trigers at the expression specified in cron 
  triggers {
    cron(cron_string)
  }
  // parameter for the pipeline
  parameters {
    string(name: 'AWS_AGENT_LABEL', defaultValue: 'any', description: 'Label of the Agent which has python3 and aws profile configured')
    string(name: 'AWS_SERVICE_CONFIG_FILE', defaultValue: './config/config.json', description: 'Path of the aws service config file')
  }

  // stages start from here
  stages {
    //  check for the ami version and if the ami is different , then go to the next stage.
    stage('check the ami version') {

      agent {
        label {
          $ {
            AWS_AGENT_LABEL
          }
        }
      }
      steps {

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

    // create the jobs dynamically
    stage("QA") {

      steps {

        createStage("kodak", "")
        createStage("content-origin", "")
        createStage("Dreamcatcher", "")
        createStage("Concierge", "")
        createStage("MUS", "")
        createStage("VMS", "")

      }

    }
  }
  post {
    always {
      echo "====++++always++++===="
    }
    success {
      echo "====++++only when successful ++++===="
    }
    failure {
      echo "====++++only when failed++++===="
    }
  }

}