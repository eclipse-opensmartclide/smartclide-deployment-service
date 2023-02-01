import os
from decouple import config

class Settings():

    def __init__(self):
        self.repositories = {
            'mongo': {
                'host': os.environ.get('MONGO_HOST', config('MONGO_HOST')),
                'port': os.environ.get('MONGO_PORT', config('MONGO_PORT')),
                'user': os.environ.get('MONGO_USER', config('MONGO_USER')),
                'password': os.environ.get('MONGO_PASSWORD',config('MONGO_PASSWORD')),
                'database': os.environ.get('MONGO_DATABASE',config('MONGO_DATABASE')),
            }, 
            'dbapi': {
                'url': os.environ.get('DBAPI_URL',config('DBAPI_URL')),
                'token': os.environ.get('DBAPI_TOKEN',config('DBAPI_TOKEN'))
            }
        }
        
        self.api = {
            'host': '0.0.0.0', 
            'port': 3000
        } 

        self.gitlab = {
            'url': os.environ.get('GITLAB_URL',config('GITLAB_URL')),
        }

        self.mom = {
            'host': os.environ.get('MOM_HOST',config('MOM_HOST')),
            'port': os.environ.get('MOM_PORT',config('MOM_PORT')),
            'user': os.environ.get('MOM_USER',config('MOM_USER')),
            'password': os.environ.get('MOM_PASSWORD',config('MOM_PASSWORD')),
        }

        self.repo_dir = '/tmp/repos/'

    def get_job_config(self, job_name, cvs_url, pipeline):
        # return """<?xml version='1.1' encoding='UTF-8'?>
        #     <project>
        #     <builders>
        #         <hudson.tasks.Shell>
        #         <command>echo $JENKINS_VERSION</command>
        #         </hudson.tasks.Shell>
        #     </builders>
        #     </project>"""
        return '''
            <flow-definition plugin="workflow-job@2.41">
            <description> holaaa </description>
            <keepDependencies>falsec</keepDependencies>
            <properties>
            <com.coravy.hudson.plugins.github.GithubProjectProperty plugin="github@1.34.1">
            <projectUrl> https://github.com/pedbermar/wellness_challenge </projectUrl>
            <displayName/>
            </com.coravy.hudson.plugins.github.GithubProjectProperty>
            </properties>
            <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.94">
                <script>
pipeline { 
    agent { dockerfile true } 
    stages { 
        stage('Test') { 
            steps { 
                sh 'node --version' 
                sh 'svn --version' 
            } 
        } 
    } 
} 
</script>
                <sandbox>true</sandbox>
            </definition>
            <triggers/>
            <authToken>z</authToken>
            <disabled>false</disabled>
            </flow-definition>
            
            '''