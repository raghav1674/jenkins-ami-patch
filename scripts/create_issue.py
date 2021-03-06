#!/bin/python3
import os
import sys
sys.path.append('.')
from json import loads

from jira.jira import JiraAPI


USERNAME = os.getenv('JIRA_USERNAME')
API_TOKEN = os.getenv("JIRA_API_TOKEN")


jira = JiraAPI(
    USERNAME, API_TOKEN, "config/jira.config.yaml")

details = loads(jira.create_issue())
print(details["key"])


