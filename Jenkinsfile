
String cron_string = "0 0 */20 * *" // cron every 20th of the month

pipeline {
  agent none
  triggers {
    cron(cron_string)
  }
  parameters {

    string(name: 'AWS_AGENT_LABEL', defaultValue: 'any', description: 'Label of the Agent which has python3 and aws profile configured')
    string(name: 'AWS_SERVICE_CONFIG_FILE', defaultValue: './config/config.json', description: 'Path of the aws service config file')
  }

  stages {
    //  check for the ami version and if the ami is different , then go to the next stage.
   
    // create the jobs dynamically
    stage('build the QA-service-01') {

      steps {


        build job: "First Job"
       
      }
    }
    post{
        always{
            echo "====++++always++++===="
        }
        success{
            echo "====++++only when successful++++===="
             node("${AWS_AGENT_LABEL}"){
              build job: "Second Job"

             }
        }
        failure{
            echo "====++++only when failed++++===="
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