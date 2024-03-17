import argparse
from github import Github
import re
import os
import sys


try:
    github_token = os.environ["GITHUB_TOKEN"]
except KeyError:
    print("Please set the 'GITHUB_TOKEN' environment variable")
    sys.exit(1)


def parser():
    parse = argparse.ArgumentParser()
    parse.add_argument('--repository', type=str, required=True,
                       help='Github repository name (e.g., scylladb/scylladb)')
    parse.add_argument('--number', type=int, required=True,
                       help='Pull request or issue number to sync labels from')
    parse.add_argument('--label', type=str, default=None, help='Label to add/remove from an issue or PR')
    parse.add_argument('--is_issue', action='store_true', help='Determined if label change is in Issue or not')
    parse.add_argument('--label_action', type=str, choices=['opened', 'labeled', 'unlabeled'], required=True, help='Sync labels action')
    return parse.parse_args()


def copy_labels_from_linked_issues(pr_number):
    pr = repo.get_pull(pr_number)
    if pr.body:
        linked_issue_numbers = set(re.findall(r'Fixes:? (?:#|https.*?/issues/)(\d+)', pr.body))
        for issue_number in linked_issue_numbers:
            try:
                issue = repo.get_issue(int(issue_number))
                for label in issue.labels:
                    pr.add_to_labels(label.name)
                print(f"Labels from issue #{issue_number} copied to PR #{pr_number}")
            except Exception as e:
                print(f"Error processing issue #{issue_number}: {e}")


def sync_labels_on_update(pr_or_issue_number, is_issue=False, label_action='opened', label=None):
    """
    Sync labels from an issue to its linked PR, or vice versa, when a new label is added.
    This function assumes that the caller knows whether the target is an issue or a PR.
    """
    target = repo.get_issue(pr_or_issue_number) if is_issue else repo.get_pull(pr_or_issue_number)
    linked_numbers = set(re.findall(r'Fixes:? (?:#|https.*?/issues/)(\d+)', target.body))
    for linked_number in linked_numbers:
        linked_target = repo.get_issue(int(linked_number)) if not is_issue else repo.get_pull(int(linked_number))
        if label_action == 'labeled' and label not in linked_target.labels:
            linked_target.add_to_labels(label)
        if label_action == 'unlabeled' and label in linked_target.labels:
            linked_target.remove_from_labels(label)
        print(f"Labels synced between issue/PR #{pr_or_issue_number} and linked issue/PR #{linked_number}")


if __name__ == "__main__":
    args = parser()
    github = Github(github_token)
    repo = github.get_repo(args.repository)
    number = args.number
    if args.label_action == 'opened':
        copy_labels_from_linked_issues(number)
    else:
        sync_labels_on_update(number, args.is_issue, args.label_action, args.label)
