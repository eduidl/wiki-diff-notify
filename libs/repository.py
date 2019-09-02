from pathlib import Path
from typing import List

import git  # type: ignore


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
