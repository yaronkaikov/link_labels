#!/usr/bin/env python3
import argparse
import os
import sys
from github import Github
import re

try:
    github_token = os.environ["GITHUB_TOKEN"]
except KeyError:
    print("Please set the 'GITHUB_TOKEN' environment variable")
    sys.exit(1)


def parser():
    parse = argparse.ArgumentParser()
    parse.add_argument('--repo', type=str, required=True, help='Github repository name (e.g., scylladb/scylladb)')
    parse.add_argument('--number', type=int, required=True, help='Pull request or issue number to sync labels from')
    parse.add_argument('--label', type=str, default=None, help='Label to add/remove from an issue or PR')
    parse.add_argument('--is_issue', action='store_true', help='Determined if label change is in Issue or not')
    parse.add_argument('--action', type=str, choices=['opened', 'labeled', 'unlabeled'], required=True, help='Sync labels action')
    return parse.parse_args()


def copy_labels_from_linked_issues(repo, pr_number):
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


def get_linked_pr_from_issue_number(repo, number):
    linked_prs = []
    for pr in repo.get_pulls(state='all'):
        if f'{number}' in pr.body:
            linked_prs.append(pr)
        else:
            break
    return linked_prs


def get_linked_issues(repo, number):
    pr = repo.get_pull(number)
    pattern = re.compile(r'Fixes:? (?:#|https.*?/issues/)(\d+)', re.IGNORECASE)
    matches = re.findall(pattern, pr.body)
    if not matches:
        raise RuntimeError("No regex matches found in the body!")
    linked_issues = []
    for match in matches:
        linked_issues.append(match)
        print(f"Found issue number: {match}")
    return linked_issues


def sync_labels(repo, number, label, action, is_issue=False):
    if is_issue:
        linked_prs_or_issues = get_linked_pr_from_issue_number(repo, number)
        target = repo.get_pull
    else:
        linked_prs_or_issues = get_linked_issues(repo, number)
        target = repo.get_issue
    for pr_or_issue_number in linked_prs_or_issues:
        if action == 'labeled':
            target(int(pr_or_issue_number.number)).add_to_labels(label)
            print(f"Label '{label}' successfully added.")
        elif action == 'unlabeled':
            target(int(pr_or_issue_number.number)).remove_from_labels(label)
            print(f"Label '{label}' successfully removed.")
        elif action == 'opened':
            copy_labels_from_linked_issues(repo, number)
        else:
            print("Invalid action. Use 'labeled', 'unlabeled' or 'opened'.")


def main():
    args = parser()
    github = Github(github_token)
    repo = github.get_repo(args.repo)
    sync_labels(repo, args.number, args.label, args.action, args.is_issue)


if __name__ == "__main__":
    main()
