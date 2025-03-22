<!--START_SECTION:locTag-->

![From%20Hello%20World%20till%20today,%20I%20have%20written](https://img.shields.io/badge/From%20Hello%20World%20till%20today,%20I%20have%20written-154222-blue)

<!--END_SECTION:locTag-->

# GitHub Lines of Code Counter (LOCounter)

**LocCounter** is a Python-based tool that calculates the total Lines of Code (LOC) across all your GitHub repositories. It can be run automatically via GitHub Actions to update your repository's README.md with a real-time LOC badge (As shown at the top of this README.md file). The script supports file exclusions, folder-specific counting, professional contributions estimation, and encrypted tracking of repository LOC changes.

## Features

- **Automated LOC Calculation** - Counts LOC for all your repositories and updates readme with a badge.
- **File & Folder Inclusion/Exclusion** - Specify file types or directories to include/exclude per repository.
- **Forked Repository Exclusion** - Skip counting LOC from forked repositories.
- **Professional Contribution Tracking** - Optionally estimate LOC from professional experience.
- **Encrypted Data Storage** - Securely stores repository LOC history using AES encryption.
- **Supports Debugging** - Option to store LOC data in an unencrypted repo_tracker.json for debugging.
- **GitHub Actions Support** - Can be scheduled to run daily using GitHub Actions.

## Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--github_username` | ✅ | None | Your GitHub username. |
| `--github_token` | ✅ | None | GitHub **Personal Access Token (PAT)** for authentication. |
| `--repo_name` | ✅ | None | The name of the GitHub repository. |
| `--section_tag` | ✅ | None | The tag in `README.md` where the LOC badge will be placed. |
| `--secret_passphrase` | ✅ | None | Passphrase for encrypting and decrypting LOC tracking data. |
| `--repo_dir` | ❌ | `repos` | **Directory** to clone repositories. |
| `--readme_path` | ❌ | `README.md` | Path to the `README.md` file to update. |
| `--track_file` | ❌ | `repo_tracker.json` | File to store encrypted LOC tracking data. |
| `--file_extensions` | ❌ | `.py,.js,.ts,.java,.cpp,.md` | Comma-separated list of file extensions to include in LOC count. |
| `--exclude_forked_repos` | ❌ | `true` | Exclude forked repositories from LOC calculations (true/false). |
| `--exclude_repos` | ❌ | `""` | Comma-separated list of repositories to exclude. |
| `--excluded_file_extensions_per_repo` | ❌ | `{}` | JSON defining file types to exclude per repo (e.g., `{"frontend_project": [".js"]}`). |
| `--included_folders_per_repo` | ❌ | `{}` | JSON defining folders to include per repo (e.g., `{"backend_project": ["src"]}`). |
| `--display_title` | ❌ | `"Lines of Code"` | Title displayed in the LOC badge (e.g., `"Total LOC"`). |
| `--record_file_extensions` | ❌ | `false` | Enable tracking of unique file extensions found in repositories. |
| `--debug_tracker` | ❌ | `true` | Save an unencrypted `repo_tracker.json` for debugging (true/false). |
| `--enable_tracking` | ❌ | `false` | Enable tracking of repository data (true/false). |
| `--professional_contrib` | ❌ | `false` | Include estimated professional contributions in the LOC count. |
| `--loc_per_day` | ❌ | `100` | Estimated number of lines of code written per workday. |
| `--work_experience` | ❌ | `1` | Number of years of professional experience. |

## Example Configurations

Exclude .js Files in frontend_project, Include Only src/ in backend_project

```json
{
    "excluded_file_extensions_per_repo": {
        "frontend_project": [".js"]
    },
    "included_folders_per_repo": {
        "backend_project": ["src"]
    }
}
```

## Section Tag

The section_tag is a placeholder in your README.md file that tells the script where to insert/update the Lines of Code (LOC) badge.

- The script searches for a section wrapped between special comments in README.md:

```md
<!--START_SECTION:LOC-->
(Existing content or previous badge)
<!--END_SECTION:LOC-->
```

- When the script runs, it replaces everything between these two tags with the latest LOC badge.
- The badge dynamically updates every time the script executes.

## Automate with GitHub Actions

To run this script automatically every night at 11:00 PM, create a .github/workflows/loc_workflow.yml file. Check the attached file for parameters.
## Installation (Locally)

**Prerequisites**

- Python 3.8+
- All mandatory requirements in `requirements.txt`

**Clone the Repository**

```sh
git clone https://github.com/your-username/LocCounter.git
cd LocCounter
```

**Install Dependencies**

```sh
pip install -r requirements.txt
```

**Usage**

The script can be run from command line using this command.

```python
python loc_counter.py --github_username YOUR_USERNAME --github_token YOUR_GITHUB_PAT \
    --repo_name YOUR_REPO_NAME --section_tag LOC \
    --secret_passphrase "your-secret-pass" --debug_tracker true
```

## License

This project is licensed under the MIT License.

## Support & Contributions

Contributions are welcome! Feel free to submit issues or pull requests.
If you like this project, give it a star ⭐ and share it!
