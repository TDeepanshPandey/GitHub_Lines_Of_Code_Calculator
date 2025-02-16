import os
import subprocess
import requests
import re
import json

class LocCounter:
    def __init__(self, config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
        
        self.github_username = config["github_username"]
        self.github_token = config["github_token"]
        self.repo_dir = config.get("repo_dir", "repos")
        self.readme_path = config.get("readme_path", "readme.md")
        self.track_file = config.get("track_file", "repo_tracker.json")
        self.loc_badge_pattern = r'!\[Lines of Code\]\(https://img.shields.io/badge/Lines%20of%20Code-[^)]*\)'
        self.file_extensions = tuple(config.get("file_extensions", [".py", ".js", ".ts", ".java", ".cpp", ".md"]))
        self.exclude_forked_repos = config.get("exclude_forked_repos", True)
        self.exclude_repos = set(config.get("exclude_repos", []))

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
        if os.path.exists(self.track_file):
            with open(self.track_file, "r") as f:
                return json.load(f)
        return {}

    def save_repo_tracker(self, data):
        with open(self.track_file, "w") as f:
            json.dump(data, f, indent=4)

    def get_latest_commit(self, repo_name):
        branches = ["main", "master"]
        for branch in branches:
            url = f"https://api.github.com/repos/{self.github_username}/{repo_name}/commits/{branch}"
            headers = {"Authorization": f"token {self.github_token}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get("sha")
        return None

    def clone_repositories(self, repos, repo_tracker):
        if not os.path.exists(self.repo_dir):
            os.makedirs(self.repo_dir)
        updated_repos = {}
        for repo_name, repo_url in repos.items():
            latest_commit = self.get_latest_commit(repo_name)
            if latest_commit and repo_tracker.get(repo_name) != latest_commit:
                repo_path = os.path.join(self.repo_dir, repo_name)
                if os.path.exists(repo_path):
                    subprocess.run(["rm", "-rf", repo_path])
                subprocess.run(["git", "clone", "--depth=1", repo_url, repo_path])
                updated_repos[repo_name] = latest_commit
            else:
                print(f"Skipping Repo {repo_name}")
        return updated_repos

    def count_lines(self, repo_name):
        total_lines = 0
        repo_path = os.path.join(self.repo_dir, repo_name)
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(self.file_extensions):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", errors="ignore") as f:
                        total_lines += sum(1 for _ in f)
        print(f"Repository: {repo_name}, Lines of Code: {total_lines}")
        return total_lines

    def update_readme(self, loc_count):
        if not os.path.exists(self.readme_path):
            return
        with open(self.readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        new_badge = f"![Lines of Code](https://img.shields.io/badge/Lines%20of%20Code-{loc_count}-blue)"
        if re.search(self.loc_badge_pattern, content):
            content = re.sub(self.loc_badge_pattern, new_badge, content)
        else:
            content += f"\n{new_badge}\n"
        with open(self.readme_path, "w", encoding="utf-8") as f:
            f.write(content)

    def run(self):
        repos = self.get_repositories()
        repo_tracker = self.load_repo_tracker()
        updated_repos = self.clone_repositories(repos, repo_tracker)
        total_loc = 0
        if updated_repos:
            for repo_name in updated_repos.keys():
                total_loc += self.count_lines(repo_name)
            self.update_readme(total_loc)
            repo_tracker.update(updated_repos)
            self.save_repo_tracker(repo_tracker)
            print(f"Total Lines of Code Across All Repositories: {total_loc}")
        else:
            print("No new updates in repositories.")

if __name__ == "__main__":
    loc_counter = LocCounter("config.json")
    loc_counter.run()
