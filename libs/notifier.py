from configparser import ConfigParser
from pathlib import Path
from typing import Dict, List

import git  # type: ignore

import slack  # type: ignore
import slack.errors  # type: ignore
from slack.web import slack_response  # type: ignore

from .channel import Channel
from .repository import Repository

ROOT: Path = Path(__file__).parent.resolve() / '..' / 'wikis'


def _get_wiki_repos() -> List[Repository]:
    return [Repository(git.Repo(path.parent, odbt=git.GitDB)) for path in ROOT.glob('*/.git')]


class WikiDiffNotifier:

    def __init__(self, config_path: Path) -> None:
        self.config: ConfigParser = ConfigParser()
        self.config.read(config_path)
        self.client: slack.WebClient = slack.WebClient(token=self.config['Slack']['APIToken'])
        self.repos: List[Repository] = _get_wiki_repos()
        self.channels: Dict[str, Channel] = Channel.get_channels(self.client)
        self.__validate_config(config_path)

    def notify(self) -> None:
        for repo in self.repos:
            forward_commits = repo.get_forward_commits()

            prev_commit = forward_commits[0]
            prev_commit_i = 0

            repo_name = self.config['NotifyTo'][repo.name]
            self.channels[repo_name].assert_not_archived(self.client)
            for i, curr_commit in enumerate(forward_commits):
                if i == 0:
                    continue
                if i + 1 < len(forward_commits) and \
                        curr_commit.author == forward_commits[i + 1].author:
                    continue
                for diff_item in prev_commit.diff(curr_commit, create_patch=True):
                    if Path(diff_item.b_path).suffix != '.md':
                        # image or other files
                        continue
                    try:
                        res = self.__upload_diff(repo, curr_commit, diff_item)
                    except slack.errors.SlackClientError:
                        repo.rollback(len(forward_commits) - prev_commit_i + 1)
                        raise
                    else:
                        if not res['ok']:
                            print(res)
                            repo.rollback(len(forward_commits) - prev_commit_i + 1)
                            raise RuntimeError('files.upload failed')

                prev_commit = curr_commit
                prev_commit_i = i

    def __upload_diff(self, repo: Repository, curr_commit: git.Commit, diff: git.Diff) -> slack_response:
        return self.client.files_upload(channels=self.config['NotifyTo'][repo.name],
                                        initial_comment=f'{diff.b_path} is updated by {curr_commit.author.name}',
                                        title=curr_commit.summary,
                                        content=diff.diff.decode(encoding='utf-8'),
                                        filetype='diff')

    def __validate_config(self, config_path: Path) -> None:
        repo_names = [repo.name for repo in self.repos]
        for repo_name, channel_name in self.config['NotifyTo'].items():
            if repo_name not in repo_names:
                raise RuntimeError(f'{ROOT / repo_name} does not exist')
            if channel_name not in self.channels:
                raise RuntimeError(f'Channel #{channel_name} does not exist or is invisible from bot or is archived')
        for repo in self.repos:
            if repo.name not in self.config['NotifyTo']:
                raise RuntimeError(f'Configuration of {repo.name} is not described in {config_path}')
        print('Validation of configuration has been done.')
