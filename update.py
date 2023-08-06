import git
import os
from time import sleep

class Update():
    def __init__(self):
        pass

    def update_software(self, repo_url, local_path):
        if os.path.exists(local_path):
            repo = git.Repo(local_path)
            origin = repo.remotes.origin

            print("Fetching changes from the repository...")
            origin.fetch()

            current_branch = repo.active_branch
            remote_branch = origin.refs[current_branch.name]

            if current_branch.commit == remote_branch.commit:
                print("Software is already up to date.")
            else:
                print("Updating software...")
                repo.git.pull()

            print("Update completed.")
        else:
            print("Local path does not exist")

        sleep(5)

if __name__ == "__main__":
    repository_url = "https://github.com/joelermantraut/photo-cabinet" 
    local_directory = "."

    updater = Update()
    updater.update_software(repository_url, local_directory)