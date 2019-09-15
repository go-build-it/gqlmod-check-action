#!/usr/local/bin/python
import gqlmod
gqlmod.enable_gql_import()

import json
import os
import pathlib
import traceback

import gqlmod.importer

import ghstatus


with open(os.environ['GITHUB_EVENT_PATH'], 'rt') as f:
    EVENT = json.load(f)

GIT_SHA = os.environ['GITHUB_SHA']

REPO_ID = EVENT['repository']['node_id']


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
    res = ghstatus.start_check_run(repo=REPO_ID, sha=GIT_SHA)
    assert not res.errors
    run_id = res.data['createCheckRun']['checkRun']['id']
    # FIXME: Handle the case if we don't have permissions

    annotations = []
    text = ""

    count = 0
    for fname, line, col, msg in scan_files():
        count += 1
        line = f"{fname}:{line}:{col}:{msg}"
        print(line)
        annotations.append({
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
        text += line + "\n"

        if len(annotations) >= 40 and run_id:
            res = ghstatus.append_check_run(
                repo=REPO_ID,
                checkrun=run_id,
                text=text,
                annotations=annotations,
            )
            assert not res.errors
            annotations = []
            text = ""

    if run_id:
        if not count:
            res = ghstatus.append_check_run(
                repo=REPO_ID,
                checkrun=run_id,
                text="No errors found\n",
            )
            assert not res.errors
        ghstatus.complete_check_run(
            repo=REPO_ID,
            checkrun=run_id,
            state='FAILURE' if count else 'SUCCESS'
        )
