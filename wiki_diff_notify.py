import argparse
from configparser import ConfigParser
from pathlib import Path
from time import sleep
from typing import Dict, List

import git  # type: ignore
import slack  # type: ignore
import slack.errors  # type: ignore
from slack.web import slack_response  # type: ignore

ROOT: Path = Path(__file__).parent.resolve() / 'wikis'


class Repository:

    def __init__(self, repo: git.Repo) -> None:
        self.repo: git.Repo = repo
        self.name: str = Path(repo.working_dir).name

    def get_forward_commits(self) -> List[git.Commit]:
        self.repo.git.checkout('master')
        prev_commit = self.repo.commit('HEAD')
        self.repo.git.pull()
        forward_commits = []
        for commit in self.repo.iter_commits():
            forward_commits.append(commit)
            if commit == prev_commit:
                break
        forward_commits.reverse()
        return forward_commits

    def rollback(self, count: int) -> None:
        self.repo.git.reset(f'HEAD~{count}', '--hard')


def _get_wiki_repos() -> List[Repository]:
    return [Repository(git.Repo(path.parent, odbt=git.GitDB)) for path in ROOT.glob('*/.git')]


class WikiDiffNotifier:

    def __init__(self, config_path: Path) -> None:
        self.config_path: Path = config_path
        self.config: ConfigParser = ConfigParser()
        self.config.read(config_path)
        self.client: slack.WebClient = slack.WebClient(token=self.config['Slack']['APIToken'])
        self.repos: List[Repository] = _get_wiki_repos()
        self.channel_name2id: Dict[str, str] = self.__get_channel_name2id()
        self.__validate_config()

    def notify(self) -> None:
        for repo in self.repos:
            forward_commits = repo.get_forward_commits()

            prev_commit = forward_commits[0]
            prev_commit_i = 0

            self.__check_channel_is_not_archived(self.config['NotifyTo'][repo.name])
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

    def __check_channel_is_not_archived(self, channel_name: str) -> None:
        res = self.client.channels_info(channel=self.channel_name2id[channel_name])
        if not res['ok']:
            print(res)
            raise RuntimeError('channels.info failed')
        if res['channel']['is_archived']:
            print(res)
            raise RuntimeError(f'Channel #{channel_name} have been archived')

    def __get_channel_name2id(self) -> Dict[str, str]:
        channel_name2id = {}

        # public channel
        res = self.client.channels_list(exclude_archived=1)
        if not res['ok']:
            print(res)
            raise RuntimeError('channels.list failed')
        for channel in res['channels']:
            channel_name2id[channel['name']] = channel['id']

        # private channel
        res = self.client.groups_list(exclude_archived=1)
        if not res['ok']:
            print(res)
            raise RuntimeError('groups.list failed')
        for gruop in res['groups']:
            channel_name2id[gruop['name']] = gruop['id']

        return channel_name2id

    def __validate_config(self) -> None:
        repo_names = [repo.name for repo in self.repos]
        for repo_name, channel_name in self.config['NotifyTo'].items():
            if repo_name not in repo_names:
                raise RuntimeError(f'{ROOT / repo_name} does not exist')
            if channel_name not in self.channel_name2id.keys():
                raise RuntimeError(f'Channel #{channel_name} does not exist or is invisible from bot or is archived')
        for repo in self.repos:
            if repo.name not in self.config['NotifyTo']:
                raise RuntimeError(f'Configuration of {repo.name} is not described in {self.config_path}')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.ini')
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    notifier = WikiDiffNotifier(config_path)
    while True:
        notifier.notify()
        sleep(5 * 60)


if __name__ == '__main__':
    main()
