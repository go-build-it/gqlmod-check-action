#!/usr/local/bin/python
import gqlmod
gqlmod.enable_gql_import()

import gqlmod.importer
import os
import pathlib


def scan_files():
    files = map(open, pathlib.Path().glob("**/*.gql"))
    for fobj in files:
        fname = fobj.name
        for err in gqlmod.importer.scan_file(fname, fobj):
            for loc in err.locations:
                yield fname, loc.line, loc.column, err.message


os.chdir(os.environ['GITHUB_WORKSPACE'])
print(os.listdir())

with gqlmod.with_provider('github', token=os.environ.get('GITHUB_TOKEN', None)):
    ...
