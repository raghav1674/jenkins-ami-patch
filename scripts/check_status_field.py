#!/bin/python3
import os
import sys
sys.path.append('.')

from jira.jira import JiraAPI
from json import loads

USERNAME = os.getenv('JIRA_USERNAME')
API_TOKEN = os.getenv("JIRA_API_TOKEN")
FIELD_PATH = os.getenv('FIELD_PATH').split(',')
TICKET_NUMBER = os.getenv('TICKET_NUMBER')

jira = JiraAPI(USERNAME, API_TOKEN, "config/jira.config.yaml")


field =loads(jira.get_field_value_from_issue(FIELD_PATH, TICKET_NUMBER))

print(list(field.values())[0].strip())
