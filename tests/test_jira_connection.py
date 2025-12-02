#!/usr/bin/env python3
import os

from jira import JIRA


def test_jira_connection():
    # Check for required environment variables
    required_vars = ["JIRA_HOST", "JIRA_EMAIL", "JIRA_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set them using:")
        print("export JIRA_HOST=your-domain.atlassian.net")
        print("export JIRA_EMAIL=your-email@domain.com")
        print("export JIRA_API_TOKEN=your-api-token")
        return

    try:
        # Initialize JIRA client (using your working configuration style)
        server = f"https://{os.getenv('JIRA_HOST')}"
        jiraOptions = {'server': server}
        jira = JIRA(options=jiraOptions, basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN")))

        # Get issues from TEST project
        issues = jira.search_issues('project = TEST ORDER BY created DESC', maxResults=5)

        print("\nLatest TEST Project Issues:")
        print("-" * 50)
        for issue in issues:
            print(f"Key: {issue.key}")
            print(f"Summary: {issue.fields.summary}")
            print(f"Status: {issue.fields.status}")
            print("-" * 50)

        print(f"\nTotal issues found: {len(issues)}")

        # Try to get TEST-1 specifically
        try:
            test_issue = jira.issue("TEST-1")
            print("\nTEST-1 Details:")
            print("-" * 50)
            print(f"Summary: {test_issue.fields.summary}")
            print(f"Description: {test_issue.fields.description}")
            print(f"Status: {test_issue.fields.status}")
            print(f"Created: {test_issue.fields.created}")
        except Exception as e:
            print(f"\nCouldn't access TEST-1: {e!s}")

    except Exception as e:
        print(f"\nError connecting to JIRA: {e!s}")
        print("Please check your environment variables and network connection.")

if __name__ == "__main__":
    test_jira_connection()
