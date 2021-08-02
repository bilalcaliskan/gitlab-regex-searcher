# Gitlab Regex Searcher
[Gitlab](https://about.gitlab.com/) currently does not have a feature like regex scanning as version [Gitlab 14](https://about.gitlab.com/gitlab-14/).
This project aims to search the whole codebase for specific pattern.

Assume that you need to search all malicious code on your codebase which secretly steals some information and mails to 
non-domain mail address. You can use that project to scan your codebase if any hardcoded email address present on your whole 
codebase.

### Prerequisites
  - [Python 3](https://www.python.org/downloads/)
  - A running [Gitlab](https://about.gitlab.com/) instance
  - A privileged [Gitlab](https://about.gitlab.com/) user with pass/token

### Usage
This project is written with Python, so all you need to do is running the below command, also you need Python 3:
```
$ python3 src/application.py
```

### Configuration
Configuration parameters are taken at the runtime as inputs:
```
gitlab_api_url              Target Gitlab instance. (ex: https://gitlab.example.com)
gitlab_username             An authorized Gitlab user which has read access
gitlab_token                An authorized Gitlab password or token which has read access
regex                       Target regex to scan codebase
```