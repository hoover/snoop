// vim: ft=groovy
properties([
  buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '3', daysToKeepStr: '', numToKeepStr: '3')),
  pipelineTriggers([[$class: 'PeriodicFolderTrigger', interval: '2d']])
])

node('cloud') {
  def cloud_image = 'https://jenkins.liquiddemo.org/job/liquidinvestigations/job/factory/job/master/lastSuccessfulBuild/artifact/cloud-x86_64-image.tar.xz'

  stage('Host Debug Information') {
    sh 'set -x && hostname && uname -a && free -h && df -h'
  }
  deleteDir()
  checkout scm
  try {
    stage('Build a Factory & Prepare Cloud Image') {
      sh 'git clone https://github.com/liquidinvestigations/factory'
      sh 'mkdir -pv factory/images/cloud-x86_64/'
      dir('factory/images/cloud-x86_64') {
        sh "wget -q $cloud_image -O tmp.tar.xz;"
        sh 'xzcat tmp.tar.xz | tar x'
        sh 'rm tmp.tar.xz'
      }
    }
    stage('Run tests') {
      sh 'factory/factory run --share .:/mnt/snoop /mnt/snoop/run_jenkins_tests.sh'
    }
  } finally {
    if (fileExists('junit.xml')) {
      junit 'junit.xml'
    }
    deleteDir()
  }
}
