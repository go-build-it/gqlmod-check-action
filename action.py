#!/usr/local/bin/python
import gqlmod
gqlmod.enable_gql_import()

import json
import os
import pathlib
import sys
import traceback

import gqlmod.importer

import ghstatus


with open(os.environ['GITHUB_EVENT_PATH'], 'rt') as f:
    EVENT = json.load(f)

GIT_SHA = os.environ['GITHUB_SHA']

REPO_ID = EVENT['repository']['node_id']


class OutputManager:
    """
    Handles the output buffer and sending things to GitHub
    """
    def __init__(self, repo_id, sha):
        self.repo_id = repo_id
        self.git_sha = sha
        self.annotations = []
        self.output = ""
        self.success = True
        self.run_id = None

    def write(self, s):
        self.output += s
        sys.stdout.write(s)
        return len(s)

    def annotate(self, fname, line, col, msg):
        self.annotations.append({
            'path': fname,
            'location': {
                'startLine': line,
                'endLine': line,
                'startColumn': col,
                'endColumn': col,
            },
            'annotationLevel': 'FAILURE',
            'message': msg,
        })
        self.success = False
        if len(self.annotations) > 40:
            self.flush()

    def __enter__(self):
        res = ghstatus.start_check_run(repo=self.repo_id, sha=self.git_sha)
        assert not res.errors
        self.run_id = res.data['createCheckRun']['checkRun']['id']
        # FIXME: Handle the case if we don't have permissions

    def __exit__(self, *_):
        if self.success:
            self.write("No problems found\n")
        self.flush()
        ghstatus.complete_check_run(
            repo=self.repo_id,
            checkrun=self.run_id,
            state='SUCCESS' if self.success else 'FAILURE'
        )

    def flush(self):
        res = ghstatus.append_check_run(
            repo=self.repo_id,
            checkrun=self.run_id,
            text=self.output,
            annotations=self.annotations,
        )
        assert not res.errors
        self.annotations = []
        self.output = ""


def scan_files():
    files = map(open, pathlib.Path().glob("**/*.gql"))
    for fobj in files:
        fname = fobj.name
        print(f"Checking {fname}")
        try:
            for err in gqlmod.importer.scan_file(fname, fobj):
                for loc in err.locations:
                    yield fname, loc.line, loc.column, err.message
        except RuntimeError as exc:
            # Probably missing provider
            # TODO: Be more specific
            yield fname, 1, 1, str(exc)
        except Exception as exc:
            traceback.print_exc()
            yield fname, 1, 1, str(exc)


os.chdir(os.environ['GITHUB_WORKSPACE'])

with gqlmod.with_provider('github', token=os.environ.get('INPUT_GITHUB_TOKEN', None)):
    with OutputManager(REPO_ID, GIT_SHA) as output:
        for fname, line, col, msg in scan_files():
            print(f"{fname}:{line}:{col}:{msg}", file=output)
            output.annotate(fname, line, col, msg)
