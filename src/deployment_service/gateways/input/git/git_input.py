
import os
import yaml
import shutil
from git.exc import GitCommandError 
from git import Repo
from deployment_service.config.logging import logger as l
from deployment_service.config.settings import Settings

class GitInputGateway(object):
    
    def __init__(self) -> None:
        settings = Settings()
        self.repo_dir = settings.repo_dir
        self.__repo = None

    def clone_repo(self, repo_url :str, branch: str) -> str:
        try: 
            repo_name = repo_url.split('/')[-1]
            if os.path.exists(f'{self.repo_dir}{repo_name}'):
                shutil.rmtree(f'{self.repo_dir}{repo_name}')
            dest_path = f'{self.repo_dir}{repo_name}'
            self.__repo = Repo.clone_from(repo_url, dest_path)        
            return dest_path
        except Exception as excp:
            l.error(f'{excp}: Failed to clone repo ')
            import traceback
            traceback.print_exc()
            raise Exception(excp.stderr)
                
    def commit_changes(self, repo_path):
        try:
            git_repo = Repo(repo_path)
            with git_repo.config_writer() as git_config:
                git_config.set_value('user', 'name', 'John Doe')
                git_config.set_value('user', 'email', 'someone@example.com')
            
            if git_repo.is_dirty(untracked_files=True):
                git_repo.remotes.origin.pull()
                git_repo.index.add(['.gitlab-ci.yml'])
                git_repo.index.commit('Add .gitlab-ci.yml')
                return True
        except Exception as ex:
            l.error(f'{ex}: Failed to update remote')
            import traceback
            traceback.print_exc()
            
    def update_remote(self, repo_path, remote_url):
        try:
            git_repo = Repo(repo_path)
            origin = git_repo.remotes[0].set_url(new_url=remote_url)
            return True

        except Exception as ex:
            l.error(f'{ex}: Failed to update remote')
            import traceback
            traceback.print_exc()

    def write_cdci_file(self, repo_path) -> bool:
        try:
            data = {
                'image': 'docker:19.03.13',     
                'variables': {
                    'DOCKER_HOST': 'tcp://localhost:2375', 
                    'DOCKER_TLS_CERTDIR': ""
                },
                'services': ['docker:19.03.13-dind'], 
                'build': {
                    'stage': 'build',
                    'script': [
                        'echo $CI_REGISTRY_PASSWORD | docker login -u $CI_REGISTRY_USER $CI_REGISTRY --password-stdin', 
                        'docker build -t $CI_REGISTRY_IMAGE .', 
                        'docker push $CI_REGISTRY_IMAGE'
                    ]
                }
            }
            f_path = f"{repo_path}/.gitlab-ci.yml"
            file = open(f_path, "w")
            yaml.dump(data, file)
            file.close()
            return f_path
        
        except Exception as ex:
            l.error(f'{ex}: Failed to write CD/CI file ')
            import traceback
            traceback.print_exc()

    def push_repository(self, repo_path, pull: bool) -> bool:
        git_repo = Repo(repo_path, search_parent_directories=True)
            # origin = git_repo.remote(name='origin')
            # origin.push()
            # # git_repo.git.branch('master')
            
        try:
            if pull:
                git_repo.remotes.origin.pull()
            git_repo.remotes.origin.push()
            return True

        except GitCommandError:
            print('DDDDDDDD')
            import pdb; pdb.set_trace()
        except Exception as ex:
            l.error(f'{ex}: Failed to push repository')
            import traceback
            traceback.print_exc()
  