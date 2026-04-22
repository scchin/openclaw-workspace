import os
import requests
from datetime import datetime

class SyncHandler:
    """
    Handles the synchronization of soul backups between local storage 
    and a private GitHub repository.
    """
    
    def __init__(self, github_token=None, repo_name=None):
        self.token = github_token
        self.repo = repo_name # Format: "username/repo-name"
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.token else {}

    def push_to_github(self, file_paths):
        """
        Uploads a list of files (e.g., chunks) to the GitHub repository.
        """
        if not self.token or not self.repo:
            raise Exception("GitHub token or repository name not configured.")

        results = []
        for path in file_paths:
            filename = os.path.basename(path)
            with open(path, 'rb') as f:
                content = f.read()
                
            # We use the GitHub Content API to create/update files
            url = f"{self.base_url}/repos/{self.repo}/contents/{filename}"
            
            # Check if file exists to get SHA for update
            res = requests.get(url, headers=self.headers)
            sha = None
            if res.status_code == 200:
                sha = res.json().get('sha')

            data = {
                "message": f"Soul Sync Backup - {datetime.now().isoformat()}",
                "content": self._to_base64(content),
                "sha": sha
            }
            
            # For simple binary uploads, base64 is required
            import base64
            data["content"] = base64.b64encode(content).decode('utf-8')

            response = requests.put(url, headers=self.headers, json=data)
            if response.status_code in [200, 201]:
                results.append(True)
            else:
                results.append(False)
        
        return results

    def pull_from_github(self, target_dir):
        """
        Lists available backups in the repo and downloads selected chunks.
        """
        if not self.token or not self.repo:
            raise Exception("GitHub token or repository name not configured.")

        # 1. List files in the repo
        url = f"{self.base_url}/repos/{self.repo}/contents/"
        res = requests.get(url, headers=self.headers)
        if res.status_code != 200:
            raise Exception("Failed to fetch repository contents.")
        
        files = res.json()
        backups = [f for f in files if "soul_backup_" in f['name']]
        return backups

    def download_file(self, filename, destination_path):
        """Downloads a specific file from the GitHub repo."""
        url = f"{self.base_url}/repos/{self.repo}/contents/{filename}"
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            import base64
            content = base64.b64decode(res.json()['content'])
            with open(destination_path, 'wb') as f:
                f.write(content)
            return True
        return False

    def _to_base64(self, content):
        import base64
        return base64.b64encode(content).decode('utf-8')
