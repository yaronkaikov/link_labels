import requests
import os
# Configuration
github_token = os.getenv('GITHUB_TOKEN')
owner = 'scylladb'
repo = 'scylladb'
pr_number = '17483'  # PR number you're interested in

# GitHub API headers
headers = {
    'Authorization': f'token {github_token}',
    'Accept': 'application/vnd.github.v3+json',
}


def check_pr_linked_issue(owner, repo, pr_number):
    """
    Checks if a PR is linked to an issue by looking at the PR description.
    """
    pr_url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
    response = requests.get(pr_url, headers=headers)
    if response.status_code == 200:
        pr_data = response.json()
        pr_body = pr_data.get('body', '')
        # Simple keyword search for linking phrases
        # This can be refined based on how your team links PRs to issues
        keywords = ['fixes', 'resolves', 'closes']
        for keyword in keywords:
            if keyword in pr_body.lower():
                return True  # Found a keyword indicating a link to an issue
        return False  # No keywords found
    else:
        raise Exception(f'Failed to fetch PR: {response.status_code}')


# Example usage
is_linked = check_pr_linked_issue(owner, repo, pr_number)
if is_linked:
    print('This PR is linked to an issue.')
else:
    print('No direct link to an issue was found in the PR description.')