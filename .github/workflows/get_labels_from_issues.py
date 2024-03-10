#!/usr/bin/env python3

import argparse
import os
import re
import sys
import requests
import json
from github import Github

try:
    github_token = os.environ["GITHUB_TOKEN"]
except KeyError:
    print("Please set the 'GITHUB_TOKEN' environment variable")
    sys.exit(1)


def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', type=str, required=True,
                        help='Github repository name (e.g., scylladb/scylladb)')
    parser.add_argument('--pr_number', type=int, required=True,
                        help='Pull request number to sync labels from linked issue')
    parser.add_argument('--label_action', type=str, choices=['new_pr', 'add_label', 'remove_label'], required=True, help='Sync labels action')
    return parser.parse_args()


def get_pr_request_body(repo, pr_number):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)
    if response.ok:
        pr_details = response.json()
        return pr_details['body']
    else:
        print("Failed to fetch PR details. Status code:", response.status_code)


def get_linked_issues(pr_body):
    pattern = re.compile(r'Fixes:? (?:#|https.*)(\d+)', re.IGNORECASE)
    matches = re.findall(pattern, pr_body)
    if not matches:
        raise RuntimeError("No regex matches found in the body!")
    issue_numbers = []
    for match in matches:
        for entry in match:
            if "#" not in entry:
                issue_number = entry
                issue_numbers.append(issue_number)
            else:
                index = entry.index("#")
                issue_number = entry[index + 1:]
                issue_numbers.append(issue_number)
                print(f"Found issue number: {issue_number}")
    return issue_numbers


def sync_labels(issue_numbers, pr_number, repo, label_action):
    print('Sync labels from Issue to linked pull request')
    github = Github(github_token)
    pull_request_labels = [label.name for label in github.get_repo(repo).get_pull(int(pr_number)).get_labels()]
    for issue_number in issue_numbers:
        issue_labels = [label.name for label in github.get_repo(repo).get_issue(int(issue_number)).get_labels()]
        if label_action == 'new_pr':
            for label in issue_labels:
                if label and label not in pull_request_labels:
                    github.get_repo(repo).get_pull(int(pr_number)).add_to_labels(label)
                    print(f"Found and added issue label: {label}")
        else:
            pull_request_labels = [label.name for label in github.get_repo(repo).get_pull(int(pr_number)).get_labels() if label.name.startswith('backport/')]
            issue_backport_label = [label.name for label in github.get_repo(repo).get_issue(int(issue_number)).get_labels() if label.name.startswith('backport/')]
            filter_pull_request_labels = [label for label in pull_request_labels if label not in issue_backport_label]
            filter_issue_labels = [label for label in issue_backport_label if label not in pull_request_labels]

            if label_action == 'add_label':
                for filter_pull_request_label in filter_pull_request_labels:
                    github.get_repo(repo).get_issue(int(issue_number)).add_to_labels(filter_pull_request_label)
                for filter_issue_label in filter_issue_labels:
                    github.get_repo(repo).get_pull(int(pr_number)).add_to_labels(filter_issue_label)

            if label_action == 'remove_label':
                if filter_pull_request_labels:
                    for label in filter_pull_request_labels:
                        github.get_repo(repo).get_issue(int(pr_number)).remove_from_labels(label)
                if filter_issue_labels:
                    for label in filter_issue_labels:
                        github.get_repo(repo).get_issue(int(issue_number)).remove_from_labels(label)
def main():
    args = parser()
    pr_number = args.pr_number
    pr_body = get_pr_request_body(args.repository, pr_number)
    issue_numbers = get_linked_issues(pr_body)
    sync_labels(issue_numbers, pr_number, args.repository, args.label_action)


if __name__ == "__main__":
    main()