"""Execute test cases for each student submission by question#,
log results.
"""
import roster_munge
import configparser
from pathlib import Path
import shutil
import tempfile
import subprocess
import sys
import re
import os
from typing import List

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def configure(filename: str) -> configparser.ConfigParser:
    """The returned object is something like a dict;
    see configparser documentation for access
    instructions
    """
    conf = configparser.ConfigParser(inline_comment_prefixes="#")
    conf.read_file(open(filename))
    return conf


def submissions_for_problem(q_name: str)  -> List[Path]:
    """Returns a list of PosixPath objects
    in alphabetical order
    """
    tr_table = roster_munge.read_table()
    submissions = Path(f"./submissions").glob(f"*_{q_name}*.py")
    additions = Path(f"./additional").glob(f"*_{q_name}*.py")
    return sorted(list(submissions) + list(additions))
                  #key=lambda p: extract_student_name(p, tr_table))

# Namepat has changed since original;
# Now paths look like
# bakerrozellcharles_123508_10266435_appt.py
namepat = re.compile(
    r"""(?P<lastname> [a-z]+) _ (?P<firstname> [a-z]+)""",
    re.VERBOSE)

def extract_student_name(path: Path, tr_table: dict) -> str:
    """We are given the path to a Canvas submission.
    We return lastname, firstname extracted from a prefix
    of that path
    """
    filename = str(path.stem)
    namepart = filename.split("_")[0]
    realname = tr_table[namepart]
    return realname

    """ Old version
    matched = namepat.search(filename)
    if matched:
        gd = matched.groupdict()
        return f"{gd['lastname']}, {gd['firstname']}"
    raise ValueError(f"Couldn't extract student name from {filename}")
    """

def check_file(submission_path: Path,
               rename_to: str,
               grading_dir: str,
               test_name: str):
    source_name = str(submission_path)
    # Execute in a temporary directory with copies
    # of support files
    tempdir = f"/tmp/{grading_dir}"
    shutil.rmtree(tempdir, ignore_errors=True)
    shutil.copytree(grading_dir, tempdir)
    dest_name = f"{tempdir}/{rename_to}"
    test_name = f"{tempdir}/{test_name}"
    shutil.copy(source_name, dest_name)

    try:

        execution = subprocess.run(["python3", test_name, "-v"],
                               cwd=tempdir,
                               capture_output=True,
                               timeout=5)
        print(f"Return code: {execution.returncode}")
        stderr = str(execution.stderr, 'utf-8', 'ignore')
        print(f"Stderr: {stderr}")
    except Exception as e:
        print(f"Interrupted:  {e}")


def excerpt(path: Path, from_pat: str, to_pat: str):
    """Print an excerpt of submitted code from
    from_pat to to_pat.
    """
    try:
        f = open(path)
        copying = False
        found = False
        for line in f:
            if re.search(from_pat, line):
                copying = True
                found = True
            if copying:
                if re.search(to_pat, line):
                    copying = False
                    break
                else:
                    print(line, end="")

        if not found:
            print("*** DID NOT FIND EXCERPT ***")
        elif copying and to_pat != "NONE":
            print(f"\n*** DID NOT FIND '{to_pat}'")
    except Exception as e:
        print("*** Exception while trying to excerpt")
        print(e)

def main():
    try:
        config = configure("grader.ini")
        problem = config["DEFAULT"]["select"]
        name_glob = config[problem]["glob"]
        canonical_name = config[problem]["canon"]
        subdir = config[problem]["dir"]
        excerpt_from = config[problem]["excerpt_from"]
        excerpt_to = config[problem]["excerpt_to"]
        test_name = config[problem]["tests"]
    except KeyError as e:
        log.warning(f"{e}\nMissing entry in grader.ini")
        sys.exit(8)

    print(f"\nProblem: {name_glob} ({canonical_name})")
    name_table = roster_munge.read_table()
    for submission in submissions_for_problem(name_glob):
        name = extract_student_name(submission, name_table)
        print("\n-----------------------------------------")
        print(f"{name} => \t{submission}")
        check_file(submission, canonical_name, subdir, test_name)
        print()
        excerpt(submission, excerpt_from, excerpt_to)
        print(f"/ {name}")
        # break # DEBUG - Testing just on first entry for each


if __name__ == "__main__":
    main()





