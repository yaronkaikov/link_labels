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
    parser.add_argument('--number', type=int, required=True,
                        help='Pull request number to sync labels from linked issue')
    parser.add_argument('--is_issue', action='store_true', help='Determined if label change is in Issue or not')
    parser.add_argument('--label_action', type=str, choices=['opened', 'labeled', 'unlabeled'], required=True, help='Sync labels action')
    return parser.parse_args()


def get_pr_request_body(repo, number):
    url = f"https://api.github.com/repos/{repo}/pulls/{number}"
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
    pattern = re.compile(r'Fixes:? (?:#|https.*?/issues/)(\d+)', re.IGNORECASE)
    matches = re.findall(pattern, pr_body)
    if not matches:
        raise RuntimeError("No regex matches found in the body!")
    issue_numbers = []
    for match in matches:
        issue_numbers.append(match)
        print(f"Found issue number: {match}")
    return issue_numbers


def get_linked_pr(repo, issue_number, token):
    query = f"repo:{repo} is:pr is:open linked:issue {issue_number}"
    url = f"https://api.github.com/search/issues?q={query}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        pr = response.json().get('items', [])
        return pr['number']
    else:
        raise Exception(f"GitHub API returned {response.status_code}: {response.text}")


def sync_labels(issue_numbers, number, repo, label_action):
    print('Sync labels from Issue to linked pull request')
    github = Github(github_token)
    for issue_number in issue_numbers:
        issue_labels = [label.name for label in github.get_repo(repo).get_issue(int(issue_number)).get_labels()]
        print(issue_labels)
        if label_action == 'opened':
            pr_labels = [label.name for label in github.get_repo(repo).get_pull(int(number)).get_labels()]
            for label in issue_labels:
                if label and label not in pr_labels:
                    github.get_repo(repo).get_pull(int(number)).add_to_labels(label)
                    print(f"Found and added issue label: {label}")
        else:
            pr_backport_labels = [label.name for label in github.get_repo(repo).get_pull(int(number)).get_labels() if label.name.startswith('backport/')]
            issue_backport_labels = [label.name for label in github.get_repo(repo).get_issue(int(issue_number)).get_labels() if label.name.startswith('backport/')]
            filter_pr_labels = [label for label in pr_backport_labels if label not in issue_backport_labels]
            filter_issue_labels = [label for label in issue_backport_labels if label not in pr_backport_labels]

            if label_action == 'labeled':
                for filter_pull_request_label in filter_pr_labels:
                    github.get_repo(repo).get_issue(int(issue_number)).add_to_labels(filter_pull_request_label)
                for filter_issue_label in filter_issue_labels:
                    github.get_repo(repo).get_pull(int(number)).add_to_labels(filter_issue_label)

            if label_action == 'unlabeled':
                if filter_pr_labels:
                    for label in filter_pr_labels:
                        github.get_repo(repo).get_issue(int(number)).remove_from_labels(label)
                if filter_issue_labels:
                    for label in filter_issue_labels:
                        github.get_repo(repo).get_issue(int(issue_number)).remove_from_labels(label)


def main():
    args = parser()
    if args.is_issue:
        pr_number = get_linked_pr(args.repository, args.number, github_token)
        # for pr in prs:
        #     number = pr['number']
        issue_numbers = args.number
    else:
        pr_number = args.number
        pr_body = get_pr_request_body(args.repository, pr_number)
        issue_numbers = get_linked_issues(pr_body)
    sync_labels(issue_numbers, pr_number, args.repository, args.label_action)


if __name__ == "__main__":
    main()
