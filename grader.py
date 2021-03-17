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
    submissions = Path(f"./submissions").glob(f"*{q_name}*.py")
    additions = Path(f"./additional").glob(f"*{q_name}*.py")
    return sorted(list(submissions) + list(additions))
                  #key=lambda p: extract_student_name(p, tr_table))

# Canvas uses (at least) two different name munging algorithms, one
# for projects and another for quizzes.
# For projects: bakerrozellcharles_123508_10266435_appt.py
# For quizzes:  baker-rozell_charles123508_question_2425285_10332159_mini_exam.py
# For a quiz with multi-part name:
# torres_gonzalez_isaias109036_question_2425285_10300987_mini_exam.py
#   (that is, surname_surname_givenname)

namepat = re.compile(r"""
    ^                       # Must match at beginning of string
    (?P<name> [-a-z_]+)     # Can match multi-part surnames, including dashes
""", re.VERBOSE
)

#
#
def extract_student_name(path: Path, tr_table: dict) -> str:
    """We are given the path to a Canvas submission.
    We return lastname, firstname extracted from a prefix
    of that path
    """
    filename = str(path.stem)
    name_match =  namepat.match(filename)
    assert name_match
    name_part = name_match.groupdict()["name"]
    name_key = name_part.translate(roster_munge.NAME_CRUSH)
    realname = tr_table[name_key]
    return realname

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

def excerpt(path: Path, units: List[str]):
    """Print excerpts of submitted code for listed units
    (class and function names)
    """
    # We are looking for any of these names, as functions or classes
    units_disjunct = "|".join(units)
    # A class, function, or method definition is the first
    # thing on a line.  It beings with "class" or "def", then
    # one or more spaces followed by the name.
    start_pat_re = f"""
         ^(?P<indent>\\s*)             # Only indentation before it
         (?P<kind>(class)|(def))\\s+   # A class or function
         (?P<unit> {units_disjunct})   # with this name
         \\W.*"""                 # Followed by anything
    start_pat = re.compile(start_pat_re, re.VERBOSE)
    log.debug(f"Unit scan pattern: '{start_pat_re}'")
    next_unit_re = """
        ^(?P<indent>\\s*)           # Only indentation before
        (?P<kind>(class)|(def))\\s+ # then a class or function
        (?P<unit>(\\w|_)+)          # then ANY unit name
        .*                          # and we don't care after that
        """
    next_unit = re.compile(next_unit_re, re.VERBOSE)
    log.debug(f"Unit end scan pattern: '{next_unit_re}'")
    try:
        f = open(path)
        lines = iter(f)  # Allows CHUNKED for loops
        for line in lines:
            log.debug(f"Scanning line {line.rstrip()}")
            found = start_pat.match(line)
            if found:
                log.debug(f"Starting unit '{found.groups()}'")
                log.debug(f"Fields: '{found.groupdict()}'")
                indent = len(found.groupdict()["indent"])
                print(line.rstrip())
                # Subsequent lines:  Stop when we see a new
                # unit that is NOT indented within current unit
                # and is NOT of interest
                for more in lines:
                    is_a_unit = next_unit.match(more)
                    if not is_a_unit:
                        print(more.rstrip())
                        continue
                    # We've hit another unit.  If it is indented
                    # within this one, we just continue
                    #DEBUG
                    log.debug(f"Next unit '{is_a_unit.groups()}'")
                    unit_dict = is_a_unit.groupdict()
                    if unit_dict["indent"]:
                        unit_indent = len(is_a_unit.groupdict()["indent"])
                        if unit_indent > indent:
                            print(more.rstrip())
                            continue
                    # It's not indented.  Is it another one we are
                    # excerpting?
                    is_of_interest = start_pat.search(more)
                    if is_of_interest:
                        print(more.rstrip())
                        continue
                    # It's a unit, not indented, and not of interest
                    break
                    # Will continue outer loop from next line
                    # (because we're using an iterator on the lines)
    except Exception as e:
        print("*** Exception while trying to excerpt")
        print(e)

# Obsolete?
def old_excerpt(path: Path, from_pat: str, to_pat: str):
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
    except Exception as e:
        print("*** Exception while trying to excerpt")
        print(e)

        if not found:
            print("*** DID NOT FIND EXCERPT ***")
        elif copying and to_pat != "NONE":
            print(f"\n*** DID NOT FIND '{to_pat}'")

def main():
    try:
        config = configure("grader.ini")
        problem = config["DEFAULT"]["select"]
        name_glob = config[problem]["glob"]
        canonical_name = config[problem]["canon"]
        subdir = config[problem]["dir"]
        # excerpt_from = config[problem]["excerpt_from"]
        # excerpt_to = config[problem]["excerpt_to"]
        units = config[problem]["excerpt_units"]
        test_name = config[problem]["tests"]
    except KeyError as e:
        log.warning(f"{e}\nMissing entry in grader.ini")
        sys.exit(8)

    print(f"\nProblem: {name_glob} ({canonical_name})")
    name_table = roster_munge.read_table()
    submissions = submissions_for_problem(name_glob)
    assert submissions, f"No match for {name_glob}"
    for submission in submissions:
        name = extract_student_name(submission, name_table)
        print("\n-----------------------------------------")
        print(f"{name} => \t{submission} (BEGIN)")
        check_file(submission, canonical_name, subdir, test_name)
        print()
        excerpt(submission, units.split(","))
        print(f"/ {name} (END)")
        # break # DEBUG - Testing just on first entry for each


if __name__ == "__main__":
    main()





