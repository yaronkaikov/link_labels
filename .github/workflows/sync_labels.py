import requests
import os


def find_linked_pr(repo, number):
    """
    Finds the linked PR(s) to a given issue.
    """
    events_url = f'https://api.github.com/repos/{repo}/issues/{number}/events'
    response = requests.get(events_url, headers=headers)
    linked_pr = []

    if response.status_code == 200:
        events = response.json()
        for event in events:
            print(event)
            # Look for 'cross-referenced' events which indicate a link to a PR
            if event['event'] == 'labeled':
                print("1")
                pr = event['labeled']['pull_request']['url']
                linked_prs.append(pr)
    else:
        print(f'Failed to fetch events: {response.status_code}')

    return linked_pr


# Example usage
issue_number = '17482'
repo_name = 'scylladb/scylladb'
github_token = os.getenv('GITHUB_TOKEN')

# GitHub API headers
headers = {
    'Authorization': f'token {github_token}',
    'Accept': 'application/vnd.github.v3+json',
}
linked_prs = find_linked_pr(repo_name, issue_number)
for pr_url in linked_prs:
    print(f'Linked PR: {pr_url}')


# from github import Github
# import os
#
#
# def sync_labels(issue_number, repo_name, github_token):
#     g = Github(github_token)
#     repo = g.get_repo(repo_name)
#     issue = repo.get_issue(number=issue_number)
#     labels = [label.name for label in issue.labels]
#
#     # Logic to find linked PR goes here
#     # This is a placeholder for demonstration
#     linked_pr_number = find_linked_pr(issue)
#     if linked_pr_number:
#         pr = repo.get_pull(linked_pr_number)
#         # Sync labels from issue to PR
#         pr.set_labels(*labels)
#
#
# def find_linked_pr(issue):
#
#     return None
#
#
# if __name__ == '__main__':
#     issue_number = '17482'
#     repo_name = 'scylladb/scylladb'
#     github_token = os.getenv('GITHUB_TOKEN')
#     sync_labels(issue_number, repo_name, github_token)
