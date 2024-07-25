import base64
import os
import re
import requests
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
import html
import logging

class Issues(BasePlugin):
    config_scheme = (
        ('configs', config_options.Type(list, required=True)),
        ('log_level', config_options.Type(str, default='INFO')),
        ('batch_limit', config_options.Type(int, default=50)),
    )

    ISSUE_ICONS = {
        'open': '''
        <svg aria-hidden="false" focusable="false" aria-label="Open issue" role="img" class="Octicon-sc-9kayk9-0 chjfbL" viewBox="0 0 16 16" width="16" height="16" fill="#57ab5a" style="display: inline-block; user-select: none; vertical-align: text-bottom; overflow: visible; transform: translateY(-5px);"><path d="M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z"></path><path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0ZM1.5 8a6.5 6.5 0 1 0 13 0 6.5 6.5 0 0 0-13 0Z"></path></svg>
        ''',
        'closed': '''
        <svg aria-hidden="false" focusable="false" aria-label="Closed as completed issue" role="img" class="Octicon-sc-9kayk9-0 fxtjEX" viewBox="0 0 16 16" width="16" height="16" fill="#986ee2" style="display: inline-block; user-select: none; vertical-align: text-bottom; overflow: visible; transform: translateY(-5px);"><path d="M11.28 6.78a.75.75 0 0 0-1.06-1.06L7.25 8.69 5.78 7.22a.75.75 0 0 0-1.06 1.06l2 2a.75.75 0 0 0 1.06 0l3.5-3.5Z"></path><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0Zm-1.5 0a6.5 6.5 0 1 0-13 0 6.5 6.5 0 0 0 13 0Z"></path></svg>
        '''
    }
    PR_ICONS = {
        'draft': '''
        <svg aria-hidden="false" focusable="false" aria-label="Draft pull request" role="img" class="Octicon-sc-9kayk9-0 epbonB" viewBox="0 0 16 16" width="14" height="14" fill="#6a737d" style="display: inline-block; user-select: none; vertical-align: text-bottom; overflow: visible; transform: translateY(-5px);">
        <path d="M3.25 1A2.25 2.25 0 0 1 4 5.372v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.251 2.251 0 0 1 3.25 1Zm9.5 14a2.25 2.25 0 1 1 0-4.5 2.25 2.25 0 0 1 0 4.5ZM2.5 3.25a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0ZM3.25 12a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm9.5 0a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5ZM14 7.5a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0Zm0-4.25a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0Z"></path>
        </svg>
        ''',
        'open': '''
            <svg aria-hidden="false" focusable="false" aria-label="Open pull request" role="img" class="Octicon-sc-9kayk9-0 chjfbL" viewBox="0 0 16 16" width="14" height="14" fill="#57ab5a" style="display: inline-block; user-select: none; vertical-align: text-bottom; overflow: visible; transform: translateY(-5px);"><path d="M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 .854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z"></path></svg>
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


    PROCESSED_MARKER = '<!--processed-->'

    def setup_logger(self):
        self.logger = logging.getLogger('mkdocs.plugins.issues')
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

    def query_graphql(self, items, headers, graphql_url):
        # Separate queries for issues, PRs, and discussions
        queries = []
        for item in items:
            owner, repo, number, item_type = item
            item_field = {
                'issue': 'issue',
                'pr': 'pullRequest',
                'discussion': 'discussion'
            }[item_type]
            item_fragment = """id title labels(first: 10) { nodes { name color } } state"""
            if item_type == "discussion":
                item_fragment = """id title labels(first: 10) { nodes { name color } } isAnswered"""
            item_key = f'{item_type}_{owner}_{repo}_{number}'
            queries.append(f"""
                {item_key}: repository(owner: \"{owner}\", name: \"{repo}\") {{
                    {item_field}(number: {number}) {{
                        {item_fragment}
                    }}
                }}
            """)
        full_query = "query {\n" + "\n".join(queries) + "\n}"

        payload = {"query": full_query}
        self.logger.debug(f"Batch querying GraphQL API: {graphql_url}\n{full_query}")
        try:
            response = requests.post(graphql_url, json=payload, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching data from GraphQL API: {e}")
            return []

        data = response.json()
        self.logger.debug(f"GraphQL API response: {data}")
        return data.get('data', {})

    def process_matches(self, markdown, pattern, item_type, icon_map, headers, graphql_url, batch_items):
        def replace_match(match):
            full_match = match.group(0)
            link_text = match.group(1) # Text inside the []
            link_url = match.group(2) # URL inside the ()
            if self.PROCESSED_MARKER in full_match:
                return full_match  # Skip already processed content

            if link_url is None:
                self.logger.warning(f"No URL found in match: {full_match}")
                return full_match

            url_match = re.search(r"([^/]+)/([^/]+)/\w+/(\d+)", link_url)
            if not url_match:
                self.logger.warning(f"No matching owner/repo/number in URL: {link_url}")
                return full_match

            owner, repo, number = url_match.groups()
            batch_items.append((owner, repo, number, item_type))
            self.logger.debug(f"Queued {item_type}: {owner}/{repo}#{number}")

            return full_match

        return pattern.sub(replace_match, markdown)

    def replace_batch_items(self, batch_items, markdown, icon_map, headers, graphql_url):
        query_result = self.query_graphql(batch_items, headers, graphql_url)

        for composite_key, item in query_result.items():
            if not isinstance(item, dict):
                continue

            self.logger.debug(f"Processing item: {item}")

            item_type, owner, repo, number = composite_key.split('_')
            
            if item_type == 'discussion':
                state = 'answered' if item.get('isAnswered', False) else 'unanswered'
            else:
                state = item.get('state', 'unknown')

            title = item.get('title', 'unknown')
            state_icon = icon_map.get(state, '❓')  # Default to question mark if state is unknown
            labels = item.get('labels', {}).get('nodes', [])
            labels_str = ''.join(
                f'<span style="background-color: #{label["color"]}; color: #fff; padding: 1px 4px; border-radius: 3px; margin-left: 4px;">{html.escape(label["name"])}</span>'
                for label in labels
            ) or ''
            state_name = state.capitalize()

            link_type = {
                'pr': 'pull',
                'issue': 'issues',
                'discussion': 'discussions'
            }[item_type]

            link_text = f"[{title}]"
            link_url = f"https://{owner}/{repo}/{link_type}/{number}"
            item_info = f'<span title="{state_name}">{state_icon}</span> {link_text}({link_url}) {labels_str} {self.PROCESSED_MARKER}'

            # Ensure the item_id is correctly identified to be replaced in the markdown
            item_id = f"{owner}/{repo}/{link_type}/{number}"
            markdown = markdown.replace(link_text, item_info)

        batch_items.clear()
        self.logger.debug(f"Markdown after replacements: {markdown}")
        return markdown

    def on_page_markdown(self, markdown, **kwargs):
        self.batch_limit = self.config.get('batch_limit', 50)

        for conf in self.config['configs']:
            token = conf['token']
            headers = {'Authorization': f'token {token}'} if token else {}

            base_url = re.escape(conf['base_url'])
            api_url = conf['api_url']
            graphql_url = conf.get('graphql_api_url', f"{api_url}/graphql")

            issue_items = []
            pr_items = []
            discussion_items = []

            # Patterns for plain URLs and markdown links
            issue_pattern = re.compile(rf'(?<!<!--processed-->)\[([^\]]*)\]\(({base_url}/[^/]+/[^/]+/issues/\d+)\)|({base_url}/[^/]+/[^/]+/issues/\d+)')
            pr_pattern = re.compile(rf'(?<!<!--processed-->)\[([^\]]*)\]\(({base_url}/[^/]+/[^/]+/pull/\d+)\)|({base_url}/[^/]+/[^/]+/pull/\d+)')
            discussion_pattern = re.compile(rf'(?<!<!--processed-->)\[([^\]]*)\]\(({base_url}/[^/]+/[^/]+/discussions/\d+)\)|({base_url}/[^/]+/[^/]+/discussions/\d+)')

            # Match Issues
            markdown = self.process_matches(markdown, issue_pattern, 'issue', self.ISSUE_ICONS, headers, graphql_url, issue_items)
            # Match PRs
            markdown = self.process_matches(markdown, pr_pattern, 'pr', self.PR_ICONS, headers, graphql_url, pr_items)
            # Match Discussions
            markdown = self.process_matches(markdown, discussion_pattern, 'discussion', self.DISCUSSION_ICONS, headers, graphql_url, discussion_items)

            # Process remaining items
            if issue_items:
                self.logger.debug("Processing remaining issue items")
                markdown = self.replace_batch_items(issue_items, markdown, self.ISSUE_ICONS, headers, graphql_url)
            if pr_items:
                self.logger.debug("Processing remaining PR items")
                markdown = self.replace_batch_items(pr_items, markdown, self.PR_ICONS, headers, graphql_url)
            if discussion_items:
                self.logger.debug("Processing remaining discussion items")
                markdown = self.replace_batch_items(discussion_items, markdown, self.DISCUSSION_ICONS, headers, graphql_url)

        return markdown

def get_status():
    return Issues
