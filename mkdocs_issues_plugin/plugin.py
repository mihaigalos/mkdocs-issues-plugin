import os
import re
import requests
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
import html
import logging

ISSUE_ICONS = {
    'open': '''
    <svg aria-hidden="false" focusable="false" aria-label="Open issue" role="img" class="Octicon-sc-9kayk9-0 chjfbL" viewBox="0 0 16 16" width="16" height="16" fill="#57ab5a" style="display: inline-block; user-select: none; vertical-align: text-bottom; overflow: visible;"><path d="M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z"></path><path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z"></path></svg>
    ''',
    'closed': '''
    <svg aria-hidden="false" focusable="false" aria-label="Closed as completed issue" role="img" class="Octicon-sc-9kayk9-0 fxtjEX" viewBox="0 0 16 16" width="16" height="16" fill="#986ee2" style="display: inline-block; user-select: none; vertical-align: text-bottom; overflow: visible;"><path d="M11.28 6.78a.75.75 0 0 0-1.06-1.06L7.25 8.69 5.78 7.22a.75.75 0 0 0-1.06 1.06l2 2a.75.75 0 0 0 1.06 0l3.5-3.5Z"></path><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0Zm-1.5 0a6.5 6.5 0 1 0-13 0 6.5 6.5 0 0 0 13 0Z"></path></svg>
    '''
}
PR_ICONS = {
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

DISCUSSION_ICONS = {
    'unanswered': '''
    <svg aria-hidden="true" height="16" viewBox="0 0 16 16" version="1.1" width="16" data-view-component="true" class="octicon octicon-check-circle color-fg-muted mr-1">
    <path fill="#9a9284" d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8Zm1.5 0a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Zm10.28-1.72-4.5 4.5a.75.75 0 0 1-1.06 0l-2-2a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018l1.47 1.47 3.97-3.97a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042Z"></path>
    </svg>
    ''',
    'answered': '''
    <svg aria-hidden="true" height="16" viewBox="0 0 16 16" version="1.1" width="16" data-view-component="true" class="octicon octicon-check-circle-fill color-fg-success mr-1">
        <path fill="#67b36a" d="M8 16A8 8 0 1 1 8 0a8 8 0 0 1 0 16Zm3.78-9.72a.751.751 0 0 0-.018-1.042.751.751 0 0 0-1.042-.018L6.75 9.19 5.28 7.72a.751.751 0 0 0-1.042.018.751.751 0 0 0-.018 1.042l2 2a.75.75 0 0 0 1.06 0Z"></path>
    </svg>
    ''',
    'closed': '''
    <svg aria-hidden="true" height="16" viewBox="0 0 16 16" version="1.1" width="16" data-view-component="true" class="octicon octicon-discussion-closed flex-items-center mr-1">
        <path d="M0 2.75C0 1.783.784 1 1.75 1h8.5c.967 0 1.75.783 1.75 1.75v5.5A1.75 1.75 0 0 1 10.25 10H7.061l-2.574 2.573A1.457 1.457 0 0 1 2 11.543V10h-.25A1.75 1.75 0 0 1 0 8.25Zm1.75-.25a.25.25 0 0 0-.25.25v5.5c0 .138.112.25.25.25h1a.75.75 0 0 1 .75.75v2.189L6.22 8.72a.747.747 0 0 1 .53-.22h3.5a.25.25 0 0 0 .25-.25v-5.5a.25.25 0 0 0-.25-.25Zm12.5 2h-.5a.75.75 0 0 1 0-1.5h.5c.967 0 1.75.783 1.75 1.75v5.5A1.75 1.75 0 0 1 14.25 12H14v1.543a1.457 1.457 0 0 1-2.487 1.03L9.22 12.28a.749.749 0 1 1 1.06-1.06l2.22 2.219V11.25a.75.75 0 0 1 .75-.75h1a.25.25 0 0 0 .25-.25v-5.5a.25.25 0 0 0-.25-.25Zm-5.47.28-3 3a.747.747 0 0 1-1.06 0l-1.5-1.5a.749.749 0 1 1 1.06-1.06l.97.969L7.72 3.72a.749.749 0 1 1 1.06 1.06Z"></path>
    </svg>
    '''
}

class Issues(BasePlugin):
    config_scheme = (
        ('configs', config_options.Type(list, required=True)),
        ('log_level', config_options.Type(str, default='INFO')),
    )

    def setup_logger(self):
        """Set up the logger based on the configuration."""
        self.logger = logging.getLogger('mkdocs.plugins.my_plugin')
        log_level = self.config['log_level'].upper()
        numeric_level = getattr(logging, log_level, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')

        logging.basicConfig(level=numeric_level)
        self.logger.setLevel(numeric_level)

        self.logger.info(f'Log level set to {log_level}')

    def on_config(self, config, **kwargs):
        self.setup_logger()
        self.logger.debug("Initializing Issues Plugin")
        for conf in self.config['configs']:
            token = conf['token']
            if token.startswith('$'):
                env_var = token[1:]
                conf['token'] = os.getenv(env_var, '')
                if not conf['token']:
                    self.logger.warning(f"Environment variable {env_var} is not set or empty.")

    def fetch_discussion_status(self, owner, repo, number, headers):
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
            repository(owner: $owner, name: $repo) {
                discussion(number: $number) {
                    title
                    isAnswered
                    labels(first: 10) {
                        nodes {
                            name
                            color
                        }
                    }
                }
            }
        }
        """
        variables = {
            "owner": owner,
            "repo": repo,
            "number": int(number)
        }
        url = "https://api.github.com/graphql"
        payload = {
            "query": query,
            "variables": variables
        }
        self.logger.debug(f"Fetching discussion from GraphQL API: {url}")
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching discussion {owner}/{repo}#{number}: {e}")
            return 'unknown', [], 'unknown'

        data = response.json()
        self.logger.debug(data)
        discussion = data['data']['repository']['discussion']
        state = "answered" if discussion.get('isAnswered', False) == True else "unanswered"
        title = discussion.get('title', 'unknown')
        labels = [
            {'name': label['name'], 'color': label['color']}
            for label in discussion['labels']['nodes']
        ]
        return state, labels, title

    def on_page_markdown(self, markdown, **kwargs):
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
            discussion_pattern = re.compile(rf'{re.escape(base_url)}/([^/]+)/([^/]+)/discussions/(\d+)' if service == 'github' else rf'{re.escape(base_url)}/([^/]+)/([^/]+)/-/discussions/(\d+)')

            self.logger.debug(f"Issue regex pattern for {base_url}: {issue_pattern.pattern}")
            self.logger.debug(f"PR regex pattern for {base_url}: {pr_pattern.pattern}")
            self.logger.debug(f"Discussion regex pattern for {base_url}: {discussion_pattern.pattern}")

            def fetch_status(owner, repo, number, item_type):
                if service == 'github':
                    if item_type in ['issue']:
                        url = f"{api_url}/repos/{owner}/{repo}/{item_type}s/{number}"
                    elif item_type == 'pr':
                        url = f"{api_url}/repos/{owner}/{repo}/pulls/{number}"
                    elif item_type == 'discussion':
                        return self.fetch_discussion_status(owner, repo, number, headers)
                elif service == 'gitlab':
                    repo_encoded = f"{owner}%2F{repo}"
                    if item_type == 'issue':
                        url = f"{api_url}/projects/{repo_encoded}/issues/{number}"
                    elif item_type == 'pr':
                        url = f"{api_url}/projects/{repo_encoded}/merge_requests/{number}"
                    elif item_type == 'discussion':
                        url = f"{api_url}/projects/{repo_encoded}/discussions/{number}"

                self.logger.debug(f"Fetching {item_type} from URL: {url}")
                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Error fetching {item_type} {owner}/{repo}#{number}: {e}")
                    return 'unknown', [], 'unknown'

                data = response.json()
                if item_type == 'discussion':
                    state = 'open'  # default, GitHub API doesn't provide specific state field for discussions
                elif item_type == 'issue':
                    state = data.get('state', 'unknown')
                elif item_type == 'pr':
                    state = data.get('state', 'unknown')
                    draft = data.get('draft', False) if service == 'github' else data.get('work_in_progress', False)
                    if draft:
                        state = 'draft'
                    elif service == 'github':
                        merged = data.get('merged_at', None) is not None
                        if merged:
                            state = 'merged'
                labels = [
                    {'name': label['name'], 'color': label['color'] if service == 'github' else '007BFF'}
                    for label in data.get('labels', [])
                ]
                title = data.get('title', 'unknown')
                return state, labels, title

            def process_matches(pattern, item_type, icon_map, link_suffix_transform_fn=None):
                nonlocal markdown
                matches = pattern.finditer(markdown)
                for match in matches:
                    owner, repo, number = match.groups()
                    self.logger.debug(f"Processing {item_type}: {owner}/{repo}#{number}")
                    state, labels, title = fetch_status(owner, repo, number, item_type)
                    state_icon = icon_map.get(state, '❓')  # Default to question mark if state is unknown
                    state_title = state.capitalize()
                    labels_str = ''.join(
                        f'<span style="background-color: #{label["color"]}; color: #fff; padding: 1px 4px; border-radius: 3px; margin-left: 4px;">{html.escape(label["name"])}</span>'
                        for label in labels
                    ) or ''

                    link = match.group(0)
                    if link_suffix_transform_fn:
                        link = link_suffix_transform_fn(link)

                    item_info = f'<span title="{state_title}">{state_icon}</span> [{title}]({link}) {labels_str}'
                    markdown = markdown.replace(match.group(0), item_info)
                    self.logger.debug(f"Processed {item_type}: {owner}/{repo}#{number} with state: {state}")

            # Process issues: GitHub or GitLab issues
            process_matches(issue_pattern, 'issue', ISSUE_ICONS)
            # Process PRs: GitHub or GitLab pull requests
            process_matches(pr_pattern, 'pr', PR_ICONS,
                            link_suffix_transform_fn=(lambda link: link.replace('/-/merge_requests/', '/merge_requests/')) if service == 'gitlab' else None)
            # Process discussions: GitHub or GitLab discussions
            process_matches(discussion_pattern, 'discussion', DISCUSSION_ICONS,
                            link_suffix_transform_fn=(lambda link: link.replace('/-/discussions/', '/discussions/')) if service == 'gitlab' else None)

        return markdown

# Setup function for entry point
def get_status():
    return Issues
