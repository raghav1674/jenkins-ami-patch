String cron_string = "0 0 */20 * *" // cron every 20th of the month

// actual pipeline 
pipeline {
  agent { label "${AWS_AGENT_LABEL}"}
  // trigers at the expression specified in cron 
  triggers {
    cron(cron_string)
  }
  // parameter for the pipeline
  parameters {
    string(name: 'AWS_AGENT_LABEL', defaultValue: 'any', description: 'Label of the Agent which has python3 and aws profile configured')
    string(name: 'AWS_SERVICE_CONFIG_FILE', defaultValue: './config/config.yaml', description: 'Path of the aws service config file')
  }

  // stages start from here
  stages {
    //  check for the ami version and if the ami is different , then go to the next stage.
    stage('check the ami version') {

      agent { label "${AWS_AGENT_LABEL}"}
      steps {
         withCredentials([
          [
            $class: 'AmazonWebServicesCredentialsBinding',
            credentialsId: "aws-creds",
            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
          ]
        ]) {
      
        sh "pip3 install -r requirements.txt"

        sh(returnStdout: true, script: 'python3 check_ami_version.py')
         
      }
      }
    }
    // create the jobs dynamically
    stage("QA") {

      steps {
         withCredentials([
          [
            $class: 'AmazonWebServicesCredentialsBinding',
            credentialsId: "aws-creds",
            accessKeyVariable: 'AWS_ACCESS_KEY_ID',
            secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
          ]
        ]) {

          sh(returnStdout: true, script: 'python3 do_instance_refresh.py')


      }
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
    }
    failure {
      echo "====++++only when failed++++===="
    }
  }

}