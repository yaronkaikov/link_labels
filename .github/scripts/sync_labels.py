#!/usr/bin/env python3

import argparse
import os
import re
import sys
import requests
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
                        help='Pull request or issue number to sync labels from')
    parser.add_argument('--label', type=str, default=None, help='Label to add/remove from an issue or PR')
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


def get_linked_issues(pr_body, repo):
    pattern = re.compile(r'Fixes:? (?:#|https.*?/issues/)(\d+)', re.IGNORECASE)
    matches = re.findall(pattern, pr_body)
    if not matches:
        raise RuntimeError("No regex matches found in the body!")
    issue_numbers = []
    for match in matches:
        issue_numbers.append(match)
        print(f"Found issue number: {match}")
    return issue_numbers


def get_linked_pr(repo, issue_number):
    for pr in repo.get_pulls(state='all'):
        if pr.body and f"#{issue_number}" in pr.body:
            print(f'PR contains {issue_number} in Body')
            print(pr.number)
            return pr.number

    # query = f"repo:{repo} is:pr is:open linked:issue {issue_number}"
    # url = f"https://api.github.com/search/issues?q={query}"
    # headers = {"Authorization": f"Bearer {token}"}
    # response = requests.get(url, headers=headers)
    # if response.ok:
    #     pr = response.json().get('items', [])
    #     return pr['number']
    # else:
    #     raise Exception(f"GitHub API returned {response.status_code}: {response.text}")


def sync_labels(issue_numbers, pr_number, repo, label_action, label, is_issue):
    print('Sync labels from Issue to linked pull request')
    for issue_number in issue_numbers:
        if label_action == 'opened':
            issue_labels = [label.name for label in repo.get_issue(issue_number).get_labels()]
            pr_labels = [label.name for label in repo.get_pull(pr_number).get_labels()]
            for label in issue_labels:
                if label and label not in pr_labels:
                    repo.get_pull(pr_number).add_to_labels(label)
                    print(f"Found and added issue label: {label}")
        else:
            if label_action == 'labeled':
                if is_issue and pr_number is not None:
                    repo.get_pull(pr_number).add_to_labels(label)
                else:
                    repo.get_issue(issue_number).add_to_labels(label)
            if label_action == 'unlabeled':
                if is_issue:
                    repo.get_pull(pr_number).remove_from_labels(label)
                else:
                    repo.get_issue(issue_number).remove_from_labels(label)


def main():
    args = parser()
    github = Github(github_token)
    repo = github.get_repo(args.repository)

    if args.is_issue:
        pr_number = get_linked_pr(repo, args.number)
        issue_numbers = [args.number]
    else:
        pr_number = args.number
        pr_body = get_pr_request_body(args.repository, pr_number)
        issue_numbers = get_linked_issues(pr_body, args.repository)
    sync_labels(issue_numbers, pr_number, repo, args.label_action, args.label, args.is_issue)


if __name__ == "__main__":
    main()
