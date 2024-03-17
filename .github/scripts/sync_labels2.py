import os
from github import Github
import re

# Replace 'your_token_here' with your actual GitHub token
g = Github(os.environ["GITHUB_TOKEN"])

# Replace 'owner/repo' with the owner and repository you're interested in
repo_name = "yaronkaikov/link_labels"
repo = g.get_repo(repo_name)


def copy_labels_from_linked_issues(pr_number):
    pr = repo.get_pull(pr_number)
    if pr.body:
        linked_issue_numbers = set(re.findall(r"#(\d+)", pr.body))
        for issue_number in linked_issue_numbers:
            try:
                issue = repo.get_issue(int(issue_number))
                for label in issue.labels:
                    pr.add_to_labels(label.name)
                print(f"Labels from issue #{issue_number} copied to PR #{pr_number}")
            except Exception as e:
                print(f"Error processing issue #{issue_number}: {e}")


def get_linked_pr_from_issue_number(number):
    linked_prs = []
    for pr in repo.get_pulls(state='all'):
        if f'{number}' in pr.body:
            linked_prs.append(pr)
        else:
            break
    pattern = re.compile(r'Fixes:? (?:#|https.*?/issues/)(\d+)', re.IGNORECASE)
    for pr in linked_prs:
        linked_numbers = re.findall(pattern, pr.body)
    print(linked_numbers)
    return linked_numbers


def sync_labels_on_update(pr_or_issue_number, is_issue=False):
    """
    Sync labels from an issue to its linked PR, or vice versa, when a new label is added.
    This function assumes that the caller knows whether the target is an issue or a PR.
    """
    if is_issue:
        linked_pr = get_linked_pr_from_issue_number(pr_or_issue_number)
    else:
        target = repo.get_pull(pr_or_issue_number)
    for linked_number in linked_numbers:
        linked_target = repo.get_issue(linked_number) if not is_issue else repo.get_pull(linked_number)
        print(linked_target.label)
        existing_labels = [label.name for label in linked_target.labels]
        for label in target.labels:
            if label.name not in existing_labels:
                linked_target.add_to_labels(label.name)
        print(f"Labels synced between issue/PR #{pr_or_issue_number} and linked issue/PR #{linked_number}")


# Example usage:
# This is for new PR only
# pr_number = 50  # Replace with the specific PR number you're interested in
# copy_labels_from_linked_issues(pr_number)


# To sync labels when a new label is added, determine whether the target is an issue or a PR and its number:
sync_labels_on_update(44, is_issue=True)  # Replace 123 with the actual PR or issue number
