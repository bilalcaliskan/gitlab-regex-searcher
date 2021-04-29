#!/usr/bin/python

import getpass
import os
import subprocess
import sys
import httplib2
import json
import sh
import re
from rm import rm
from sh import git
from git import Repo, InvalidGitRepositoryError
import logging
import logging.handlers


def init_logger():
    handler = logging.handlers.WatchedFileHandler("gitlab-regex-searcher.log")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    root.addHandler(handler)


def search_by_regex(directory, regex, repo):
    r = Repo(directory)
    g = r.git
    branches = get_all_branches()
    if len(branches) > 1:
        for branch in branches:
            if "HEAD" not in branch and "master" in branch:
                g.checkout(branch)
                for dir_name, dirs, files in os.walk(directory):
                    for file_name in files:
                        file_path = os.path.join(dir_name, file_name)
                        try:
                            with open(file_path) as f:
                                if ".git" not in file_path:
                                    data = f.read()
                                    is_matched = re.search(regex, data)
                                    if is_matched:
                                        logging.warning("FOUND {item} on file {file} on repo {repo} on branch {branch}!"
                                                        .format(item=is_matched.group(), file=file_name,
                                                                repo=repo,
                                                                branch=r.active_branch))
                        except UnicodeDecodeError:
                            pass


def delete_directory(directory):
    rm(os.path.abspath(directory))


def get_revision_list():
    return git('rev-list', '--all').strip().split('\n')


def get_all_branches():
    cmd = "git branch -r | grep -v 'master|dynamic' | awk -F '/' '{print $2}'"
    status, output = subprocess.getstatusoutput(cmd)
    branches = []
    if status == 0:
        branches += output.split("\n")
    return branches


def get_all_repos(gitlab_url, gitlab_token):
    page_count = 10
    item_per_page = 100
    data = []
    for i in range(1, page_count):
        paging_parameters = "?per_page={item_per_page}&page={page_number}".format(item_per_page=item_per_page,
                                                                                  page_number=i)
        api_url = "{url}/api/v4/projects{params}".format(url=gitlab_url, params=paging_parameters)
        headers = {'Private-Token': gitlab_token}
        http = httplib2.Http(disable_ssl_certificate_validation=True)
        response, content = http.request(api_url, 'GET', headers=headers)
        if response.status == 200:
            tmp = json.loads(content)
            for repo in tmp:
                data.append(repo.get("path_with_namespace"))
        else:
            raise Exception("Getting all repos failed: response code:" + str(response.status) + ", message=" + content)
    return data


def get_immediate_subdirectories():
    return set([fname for fname in os.listdir('.') if os.path.isdir(fname)])


def clone(link):
    repo_path: None
    if link is not None:
        try:
            pre_path = get_immediate_subdirectories()
            git("clone", link)
            post_path = get_immediate_subdirectories()
            repo_path = (post_path - pre_path).pop()
            os.chdir(repo_path)
        except sh.ErrorReturnCode_128:
            pass
    else:
        logging.error("Clone link must be specified!")


def skip_ssl_verify():
    git("config", "--global", "http.sslVerify", "false")


def main():
    init_logger()
    base_directory = os.getcwd()
    scanned_repo_count = 0
    gitlab_api_url = input("Git API url: ")
    if "http" not in gitlab_api_url or "https" not in gitlab_api_url:
        print("gitlab_api_url must contain protocol like http or https, exiting!")
        sys.exit(255)
    if "https" in gitlab_api_url:
        skip_ssl_verify()
    gitlab_protocol = gitlab_api_url.split("://")[0]
    gitlab_clone_url = gitlab_api_url.split("://")[1]
    gitlab_username = input("Git username: ")
    # to be able to clone from repository, an access token is needed with read_repository as a scope
    # https://docs.gitlab.com/ee/user/project/deploy_tokens/#git-clone-a-repository
    gitlab_token = getpass.getpass(prompt="Git API token: ", stream=None)
    regex = input("Regex to search: ")
    repos = get_all_repos(gitlab_url=gitlab_api_url, gitlab_token=gitlab_token)
    for repo in repos:
        try:
            clone(link="{protocol}://{username}:{token}@{url}/{repo}.git"
                  .format(username=gitlab_username,
                          token=gitlab_token,
                          protocol=gitlab_protocol,
                          url=gitlab_clone_url,
                          repo=repo))
            search_by_regex(directory=os.getcwd(), regex="{regex}".format(regex=regex), repo=repo)
            scanned_repo_count += 1
            delete_directory(directory=os.getcwd())
            os.chdir(base_directory)
        except InvalidGitRepositoryError:
            logging.error("InvalidGitRepositoryError raised for repo {repo}, skipping...".format(repo=repo))
            continue
    logging.warning("Total scanned repo count = {repo_count}".format(repo_count=scanned_repo_count))


if __name__ == "__main__":
    if not len(sys.argv) == 1:
        sys.exit(-1)
    main()
