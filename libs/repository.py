import os
from pathlib import Path
import subprocess
from typing import List

import git  # type: ignore


class Repository:

    def __init__(self, repo: git.Repo) -> None:
        self.repo: git.Repo = repo
        self.name: str = Path(repo.working_dir).name

    def get_forward_commits(self) -> List[git.Commit]:
        self.repo.git.checkout('master')
        prev_commit = self.repo.commit('HEAD')
        """
        HACK: self.repo.pull() does not work well. (sometimes fails)"
        Error message is as follows.

        git.exc.GitCommandError: Cmd('git') failed due to: exit code(1)
          cmdline: git pull
          stderr: 'Internal API unreachable
        fatal: Could not read from remote repository.

        Please make sure you have the correct access rights
        and the repository exists.'
        """
        # self.repo.pull()
        os.chdir(self.repo.working_dir)
        subprocess.run('git pull origin master'.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        forward_commits = []
        for commit in self.repo.iter_commits():
            forward_commits.append(commit)
            if commit == prev_commit:
                break
        forward_commits.reverse()
        return forward_commits

    def rollback(self, count: int) -> None:
        self.repo.git.reset(f'HEAD~{count}', '--hard')
