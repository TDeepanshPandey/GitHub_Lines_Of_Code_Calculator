import os
import subprocess
import requests
import re
import json
import argparse
from Crypto.Cipher import AES
import base64
import hashlib

class LocCounter:
    
    def __init__(self, args):
        self.github_username = args.github_username
        self.github_token = args.github_token
        self.repo_dir = args.repo_dir
        self.readme_path = args.readme_path
        self.file_extensions = tuple(args.file_extensions.split(','))
        self.exclude_forked_repos = args.exclude_forked_repos.lower() == 'true'
        self.exclude_repos = set(args.exclude_repos.split(',')) if args.exclude_repos else set()
        self.record_file_extensions = args.record_file_extensions
        self.all_file_extensions = set()
        self.section_tag = args.section_tag
        self.secure_dir = ".secure_data"
        os.makedirs(self.secure_dir, exist_ok=True)
        self.track_file = os.path.join(self.secure_dir, args.track_file)
        self.SECRET_KEY = args.secret_passphrase
        self.debug_tracker = args.debug_tracker
        self.excluded_file_extensions_per_repo = args.excluded_file_extensions_per_repo
        self.display_title = args.display_title.replace(" ", "%20")
        self.included_folders_per_repo = args.included_folders_per_repo
        self.loc_per_day = args.loc_per_day
        self.work_experience = args.work_experience
        self.professional_contrib = args.professional_contrib

    def encrypt(self, data):
        """ Encrypts data using AES """
        key = hashlib.sha256(self.SECRET_KEY.encode()).digest()
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

    def decrypt(self, encrypted_data):
        """ Decrypts AES-encrypted data """
        key = hashlib.sha256(self.SECRET_KEY.encode()).digest()
        encrypted_data = base64.b64decode(encrypted_data)
        nonce, tag, ciphertext = encrypted_data[:16], encrypted_data[16:32], encrypted_data[32:]
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode()
    
    def get_repositories(self):
        repos = {}
        page = 1
        while True:
            url = "https://api.github.com/user/repos"
            headers = {"Authorization": f"token {self.github_token}"}
            params = {"per_page": 100, "page": page}
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print("Failed to fetch repositories")
                break
            data = response.json()
            if not data:
                break
            for repo in data:
                if self.exclude_forked_repos and repo.get("fork", False):
                    continue
                if repo["name"] in self.exclude_repos:
                    continue
                repos[repo["name"]] = repo["clone_url"]
            page += 1
        print(f"Total repositories fetched: {len(repos)}")
        return repos

    def load_repo_tracker(self):
        """Loads repo tracker from debug file if debug mode is enabled, otherwise decrypts and loads the encrypted file."""
        path = "repo_tracker_debug.json" if self.debug_tracker else self.track_file
        if os.path.exists(path):
            with open(path, "rb" if not self.debug_tracker else "r", encoding="utf-8") as f:
                return json.load(f) if self.debug_tracker else json.loads(self.decrypt(f.read()))
        return {}

    
    def save_repo_tracker(self, data):
        """ Encrypts and saves the repo tracker securely """
        encrypted_data = self.encrypt(json.dumps(data))
        with open(self.track_file, "wb") as f:
            f.write(encrypted_data.encode())
        if self.debug_tracker:
            debug_path = os.path.join("repo_tracker_debug.json")
            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(f"Debug mode enabled: Saved unencrypted repo tracker to {debug_path}")

    def get_latest_commit(self, repo_name):
        branches = ["main", "master"]
        for branch in branches:
            url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/commits/{branch}"
            headers = {"Authorization": f"token {self.github_token}"}
            response = requests.get(url, headers=headers)
        return response.json().get("sha") if response.status_code == 200 else None

    def clone_repositories(self, repos, repo_tracker):
        if not os.path.exists(self.repo_dir):
            os.makedirs(self.repo_dir)
        updated_repos = {}

        for repo_name, repo_url in repos.items():
            latest_commit = self.get_latest_commit(repo_name)

            # If commit is None in tracker but lines exist, assume no new updates and skip cloning
            if latest_commit is None and repo_name in repo_tracker and repo_tracker[repo_name].get("lines", 0) > 0:
                # print(f"Skipping repo {repo_name} (no commit but lines exist)")
                continue
        
            if latest_commit is None or repo_name not in repo_tracker or repo_tracker[repo_name]["commit"] != latest_commit:
                # print(f"Cloning repo: {repo_name}")  # Debugging message
                repo_path = os.path.join(self.repo_dir, repo_name)
                if os.path.exists(repo_path):
                    subprocess.run(["rm", "-rf", repo_path])
                subprocess.run(["git", "clone", "--depth=1", repo_url, repo_path])
                updated_repos[repo_name] = {"commit": latest_commit, "lines": 0}
            # else:
                # print(f"Skipping Repo {repo_name}")  # Debugging message
        return updated_repos


    def count_lines(self, repo_name):
        """Counts total lines of code for a repository, applying per-repo file exclusions and folder restrictions."""
        total_lines = 0
        repo_path = os.path.join(self.repo_dir, repo_name)

        # Get repository-specific file and folder exclusions
        excluded_extensions = self.excluded_file_extensions_per_repo.get(repo_name, [])
        included_folders = self.included_folders_per_repo.get(repo_name, [])

        for root, _, files in os.walk(repo_path, topdown=True):
            if ".git" in root.split(os.sep):
                continue

            # If specific folders are defined for this repo, only scan them
            if included_folders:
                relative_root = os.path.relpath(root, repo_path)
                if not any(relative_root.startswith(folder) for folder in included_folders):
                    continue  # Skip this folder if it's not in the included list

            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[-1]  # Get file extension

                # Skip excluded file types for this repository
                if file_ext in excluded_extensions:
                    continue

                # Record unique file extensions if enabled
                if self.record_file_extensions and file_ext:
                    self.all_file_extensions.add(file_ext)

                # Special handling for .ipynb files (only count code cells)
                if file_ext == ".ipynb":
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            notebook = json.load(f)
                        for cell in notebook.get("cells", []):
                            if cell.get("cell_type") == "code":
                                total_lines += len(cell.get("source", []))
                    except (json.JSONDecodeError, KeyError):
                        continue  # Skip if JSON is invalid
                elif file_ext in self.file_extensions:
                    with open(file_path, "r", errors="ignore") as f:
                        total_lines += sum(1 for _ in f)

        return total_lines



    def update_readme(self, total_loc):
            if not os.path.exists(self.readme_path):
                return
            with open(self.readme_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = re.sub(
                f'<!--START_SECTION:{self.section_tag}-->.*?<!--END_SECTION:{self.section_tag}-->',
                f'<!--START_SECTION:{self.section_tag}-->\n\n'
                f'![{self.display_title}](https://img.shields.io/badge/{self.display_title}-{total_loc}-blue)\n\n'
                f'<!--END_SECTION:{self.section_tag}-->',
                content, flags=re.DOTALL
            )
            with open(self.readme_path, "w", encoding="utf-8") as f:
                f.write(new_content)
                
    def run(self):
        repos = self.get_repositories()
        repo_tracker = self.load_repo_tracker()
        updated_repos = self.clone_repositories(repos, repo_tracker)
        total_loc = sum(repo_tracker[repo]["lines"] for repo in repo_tracker if "lines" in repo_tracker[repo])
        
            # Add professional contribution if enabled
        if self.professional_contrib:
            work_days = self.work_experience * 261  # Approximate total work days
            professional_loc = self.loc_per_day * work_days
            total_loc += professional_loc
            print(f"Professionally I have written {professional_loc}")
        
        for repo_name in updated_repos.keys():
            loc_count = self.count_lines(repo_name)
            total_loc += loc_count
            updated_repos[repo_name]["lines"] = loc_count
        
        if self.record_file_extensions:
            print(f"All Unique File Extension in your Github: {self.all_file_extensions}")
        repo_tracker.update(updated_repos)
        self.save_repo_tracker(repo_tracker)
        self.update_readme(total_loc)
        print(f"Total Lines of Code Across All Repositories: {total_loc}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate and track total lines of code across GitHub repositories.")

    # Required arguments
    parser.add_argument("--github_username", required=True, help="Your GitHub username.")
    parser.add_argument("--github_token", required=True, help="GitHub Personal Access Token (PAT) for authentication.")
    parser.add_argument("--section_tag", required=True,  help="The tag to identify the section in README where the LOC badge is placed.")
    parser.add_argument("--secret_passphrase", required=True, help="Secret passphrase used for encrypting and decrypting repository tracking data.")

    # Repository and file settings
    parser.add_argument("--repo_dir", default="repos", help="Local directory where repositories will be cloned.")
    parser.add_argument("--readme_path", default="readme.md", help="Path to the README file where the LOC badge will be updated.")
    parser.add_argument("--track_file", default="repo_tracker.json", help="Filename to store encrypted repository tracking data.")
    parser.add_argument("--file_extensions", default=".py,.js,.ts,.java,.cpp,.md", help="Comma-separated list of file extensions to include in LOC calculations.")
    parser.add_argument("--exclude_forked_repos", default="true", help="Exclude forked repositories from LOC calculations (true/false).")
    parser.add_argument("--exclude_repos", default="", help="Comma-separated list of repositories to exclude from LOC calculations.")
    parser.add_argument("--excluded_file_extensions_per_repo", type=json.loads, default="{}", help="Specify repository-specific file exclusions as a JSON string (e.g., '{\"repo_name\": [\".js\", \".css\"]}').")
    parser.add_argument("--included_folders_per_repo", type=json.loads, default="{}", help="Specify repository-specific folder inclusions as a JSON string (e.g., '{\"repo_name\": [\"src\", \"lib\"]}').")

    # Display settings
    parser.add_argument("--display_title", default="Lines of Code", help="Title displayed in the LOC badge (e.g., 'Total LOC').")

    # Debugging and tracking
    parser.add_argument("--record_file_extensions", default=False, action="store_true", help="Enable tracking of unique file extensions found in repositories.")
    parser.add_argument("--debug_tracker", default=False, help="Save an unencrypted repo_tracker.json for debugging (true/false).")

    # Professional contribution estimation
    parser.add_argument("--professional_contrib", action="store_true", help="Include estimated professional contributions in the LOC count.")
    parser.add_argument("--loc_per_day", type=int, default=100, help="Estimated number of lines of code written per working day (only used if professional_contrib is enabled).")
    parser.add_argument("--work_experience", type=int, default=1, help="Number of years of professional experience (only used if professional_contrib is enabled).")

    args = parser.parse_args()

    # Validate that --loc_per_day and --work_experience are provided if --professional_contrib is enabled
    if args.professional_contrib and (args.loc_per_day is None or args.work_experience is None):
        parser.error("--loc_per_day and --work_experience must be provided when --professional_contrib is enabled.")

    loc_counter = LocCounter(args)
    loc_counter.run()
