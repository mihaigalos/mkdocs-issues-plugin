import os
import re
import requests
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
import html
import logging

logger = logging.getLogger('mkdocs.plugins.issues')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

# Define SVG icons with appropriate colors for each status
SVG_ICONS = {
    'draft': '''
        <svg aria-hidden="false" focusable="false" aria-label="Draft pull request" role="img" class="Octicon-sc-9kayk9-0 epbonB" viewBox="0 0 16 16" width="14" height="14" fill="#6a737d" style="display: inline-block; user-select: none; vertical-align: text-bottom; overflow: visible;"><path d="M3.25 1A2.25 2.25 0 0 1 4 5.372v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.251 2.251 0 0 1 3.25 1Zm9.5 14a2.25 2.25 0 1 1 0-4.5 2.25 2.25 0 0 1 0 4.5ZM2.5 3.25a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0ZM3.25 12a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm9.5 0a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5ZM14 7.5a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0Zm0-4.25a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0Z"></path></svg>
    ''',
    'open': '''
        <svg aria-hidden="false" focusable="false" aria-label="Open pull request" role="img" class="Octicon-sc-9kayk9-0 chjfbL" viewBox="0 0 16 16" width="14" height="14" fill="#57ab5a" style="display: inline-block; user-select: none; vertical-align: text-bottom; overflow: visible;"><path d="M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z"></path></svg>
    ''',
    'closed': '''
        <svg class="octicon octicon-git-pull-request-closed closed" title="Closed" aria-label="Closed Pull Request" viewBox="0 0 16 16" version="1.1" width="16" height="16" role="img"><path fill="#d73a49" d="M3.25 1A2.25 2.25 0 0 1 4 5.372v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.251 2.251 0 0 1 3.25 1Zm9.5 5.5a.75.75 0 0 1 .75.75v3.378a2.251 2.251 0 1 1-1.5 0V7.25a.75.75 0 0 1 .75-.75Zm-2.03-5.273a.75.75 0 0 1 1.06 0l.97.97.97-.97a.748.748 0 0 1 1.265.332.75.75 0 0 1-.205.729l-.97.97.97.97a.751.751 0 0 1-.018 1.042.751.751 0 0 1-1.042.018l-.97-.97-.97.97a.749.749 0 0 1-1.275-.326.749.749 0 0 1 .215-.734l.97-.97-.97-.97a.75.75 0 0 1 0-1.06ZM2.5 3.25a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0ZM3.25 12a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm9.5 0a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Z"></path></svg>
    ''',
    'merged': '''
    <svg class="octicon octicon-git-merge merged" title="Merged" aria-label="Merged Pull Request" viewBox="0 0 16 16" version="1.1" width="16" height="16" role="img"><path fill="#6f42c1" d="M5.45 5.154A4.25 4.25 0 0 0 9.25 7.5h1.378a2.251 2.251 0 1 1 0 1.5H9.25A5.734 5.734 0 0 1 5 7.123v3.505a2.25 2.25 0 1 1-1.5 0V5.372a2.25 2.25 0 1 1 1.95-.218ZM4.25 13.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm8.5-4.5a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5ZM5 3.25a.75.75 0 1 0 0 .005V3.25Z"></path></svg>
    '''
}

class Issues(BasePlugin):
    config_scheme = (
        ('configs', config_options.Type(list, required=True)),
    )

    def on_config(self, config, **kwargs):
        logger.debug("Initializing Issues Plugin")
        for conf in self.config['configs']:
            token = conf['token']
            if token.startswith('$'):
                env_var = token[1:]
                conf['token'] = os.getenv(env_var, '')
                if not conf['token']:
                    logger.warning(f"Environment variable {env_var} is not set or empty.")

    def on_page_markdown(self, markdown, **kwargs):
        logger.debug("Processing page markdown")
        for conf in self.config['configs']:
            service = conf['service']
            base_url = conf['base_url']
            api_url = conf['api_url']
            token = conf['token']
            headers = {'Authorization': f'token {token}'} if token else {}
            if service == 'gitlab':
                headers = {'Private-Token': token} if token else {}

            issue_pattern = re.compile(rf'{re.escape(base_url)}/([^/]+)/([^/]+)/issues/(\d+)' if service == 'github' else rf'{re.escape(base_url)}/([^/]+)/([^/]+)/-/issues/(\d+)')
            pr_pattern = re.compile(rf'{re.escape(base_url)}/([^/]+)/([^/]+)/pull/(\d+)' if service == 'github' else rf'{re.escape(base_url)}/([^/]+)/([^/]+)/-/merge_requests/(\d+)')
            logger.debug(f"Issue regex pattern for {base_url}: {issue_pattern.pattern}")
            logger.debug(f"PR regex pattern for {base_url}: {pr_pattern.pattern}")

            def fetch_issue_status(owner, repo, number):
                if service == 'github':
                    url = f"{api_url}/repos/{owner}/{repo}/issues/{number}"
                elif service == 'gitlab':
                    repo_encoded = f"{owner}%2F{repo}"
                    url = f"{api_url}/projects/{repo_encoded}/issues/{number}"

                logger.debug(f"Fetching issue from URL: {url}")
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error fetching issue {owner}/{repo}#{number}: {e}")
                    return 'unknown', []

                issue = response.json()
                status = issue.get('state', 'unknown')
                labels = [
                    {'name': label['name'], 'color': label['color'] if service == 'github' else '007BFF'}
                    for label in issue.get('labels', [])
                ]
                return status, labels

            def fetch_pr_status(owner, repo, number):
                if service == 'github':
                    pr_url = f"{api_url}/repos/{owner}/{repo}/pulls/{number}"
                    issue_url = f"{api_url}/repos/{owner}/{repo}/issues/{number}"
                elif service == 'gitlab':
                    repo_encoded = f"{owner}%2F{repo}"
                    pr_url = f"{api_url}/projects/{repo_encoded}/merge_requests/{number}"
                    issue_url = pr_url

                logger.debug(f"Fetching PR from URL: {pr_url}")
                try:
                    response = requests.get(pr_url, headers=headers)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error fetching PR {owner}/{repo}#{number}: {e}")
                    return 'unknown', []

                pr = response.json()
                status = pr.get('state', 'unknown')
                draft = pr.get('draft', False) if service == 'github' else pr.get('work_in_progress', False)
                if draft:
                    status = 'draft'
                elif service == 'github':
                    merged = pr.get('merged_at', None) is not None
                    if merged:
                        status = 'merged'
                    elif status == 'closed':
                        status = 'closed'
                elif service == 'gitlab':
                    if pr.get('merged_at', False):
                        status = 'merged'
                    elif pr['state'] == 'closed':
                        status = 'closed'

                # Fetch labels
                labels = []
                if service == 'github':
                    try:
                        issue_response = requests.get(issue_url, headers=headers)
                        issue_response.raise_for_status()
                        issue = issue_response.json()
                        labels = [
                            {'name': label['name'], 'color': label['color']}
                            for label in issue.get('labels', [])
                        ]
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Error fetching labels for PR {owner}/{repo}#{number}: {e}")
                elif service == 'gitlab':
                    labels = [
                        {'name': label.get('name', ''), 'color': '007BFF'}
                        for label in pr.get('labels', [])
                    ]

                return status, labels

            def process_matches(pattern, fetch_status_fn, icon_map, link_suffix_transform_fn=None):
                nonlocal markdown
                matches = pattern.finditer(markdown)
                for match in matches:
                    owner, repo, number = match.groups()
                    logger.debug(f"Processing {fetch_status_fn.__name__.split('_')[1]}: {owner}/{repo}#{number}")
                    status, labels = fetch_status_fn(owner, repo, number)
                    status_icon = icon_map.get(status, '🔴')
                    status_title = status.capitalize() if status in icon_map else 'Closed'
                    labels_str = ''.join(
                        f'<span style="background-color: #{label["color"]}; color: #fff; padding: 1px 4px; border-radius: 3px; margin-left: 4px;">{html.escape(label["name"])}</span>'
                        for label in labels
                    ) or ''

                    link = match.group(0)
                    if link_suffix_transform_fn:
                        link = link_suffix_transform_fn(link)

                    if service == 'github' and fetch_status_fn == fetch_pr_status:
                        status_icon = SVG_ICONS.get(status, SVG_ICONS['closed'])
                        issue_info = f'<span title="{status_title}">{status_icon}</span> [{owner}/{repo}#{number}]({link}) {labels_str}'
                    else:
                        issue_info = f'<span title="{status_title}">{status_icon}</span> [{owner}/{repo}#{number}]({link}) {labels_str}'

                    markdown = markdown.replace(match.group(0), issue_info)
                    logger.debug(f"Processed {fetch_status_fn.__name__.split('_')[1]}: {owner}/{repo}#{number} with status: {status}")

            # Process issues
            process_matches(issue_pattern, fetch_issue_status, {'open': '🟢', 'closed': '🔴'})
            # Process PRs
            process_matches(pr_pattern, fetch_pr_status, {'open': '🟢', 'merged': '🟣', 'draft': '🟠', 'closed': '🔴'},
                            link_suffix_transform_fn=(lambda link: link.replace('/-/merge_requests/', '/merge_requests/')) if service == 'gitlab' else None)

        return markdown

# Setup function for entry point
def get_status():
    return Issues

