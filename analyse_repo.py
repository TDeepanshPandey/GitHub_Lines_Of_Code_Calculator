import os

def analyze_repository(repo_path):
    """Analyzes a repository to count files and total lines per file type."""
    file_counts = {}
    line_counts = {}

    for root, _, files in os.walk(repo_path):
        for file in files:
            file_ext = os.path.splitext(file)[-1]  # Get file extension
            file_ext = file_ext if file_ext else "NO_EXTENSION"

            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", errors="ignore") as f:
                    lines = sum(1 for _ in f)
            except Exception:
                continue  # Ignore files that can't be read

            file_counts[file_ext] = file_counts.get(file_ext, 0) + 1
            line_counts[file_ext] = line_counts.get(file_ext, 0) + lines

    # Print analysis results
    print("\nRepository Analysis")
    print("=" * 40)
    for ext, count in sorted(file_counts.items(), key=lambda x: -x[1]):
        print(f"{ext}: {count} files, {line_counts.get(ext, 0)} lines")

    print("=" * 40)
    print(f"Total Files: {sum(file_counts.values())}")
    print(f"Total Lines: {sum(line_counts.values())}")

# Run the script
repo_path = input("Enter the path to the repository: ").strip()
if os.path.exists(repo_path):
    analyze_repository(repo_path)
else:
    print("Invalid repository path")
