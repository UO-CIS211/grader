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
from typing import List, Tuple

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


def submissions_for_problem(q_name: List[str], dir="submissions")  -> List[Tuple[str, List[Path]]]:
    """q_name could be ["expr", "codegen_context"]
    Corresponding element in result could be
    ("Garcia Perez, Salvador", ["garciaperezsalvador_106692_10867445_expr-2.py",
                                "garciaperezsalvador_106692_10867446_codegen_context.py"])
    """
    tr_table = roster_munge.read_table()
    submission_lists = []
    for pattern in q_name:
        glob_pat = f"*{pattern}*.py"
        submissions = list(Path(f"./{dir}").glob(glob_pat))
        if submissions:
            log.debug(f"globbed '{glob_pat}' in ./{dir}, got {submissions}")
        else:
            log.warning(f"Did not find ./{dir}, or nothing there matching {glob_pat}")
        additions = list(Path(f"./additional").glob(f"*{pattern}*.py"))
        column = [(extract_student_name(p, tr_table), p) for p in submissions + additions]
        submission_lists.append(sorted(column))
    # Now we should have a column for each file, in the order they appear in q_name
    # Each entry in each column is (name, path)
    # We need to join them on student name.
    log.debug(f"\n***\nSubmissions before joining: {submission_lists}")
    submissions = join_columns(submission_lists)
    log.debug(f"\n***\nJoined submissions: {submissions}")
    # Bug fix:  Some students didn't turn in some components of an assignment.
    # Filter incomplete submissions
    filtered = []
    for student, paths in submissions:
        if None in paths:
            print(f"Incomplete submission for {student}")
        else:
            filtered.append((student, paths))
    return filtered

def select_submissions(submissions: list[str, list],
                       from_prefix: str, to_prefix: str
                       ) -> list[str, list]:
    """Select a subset of submissions by prefix of student name, e.g., "A"-"F"
    Selection is inclusive and normalized to upper case, so a-f includes
    "Albertson" and "Fernandez".
    """
    selected = []
    from_prefix = from_prefix.upper()
    sentinel = to_prefix.upper() + "zzz"
    assert from_prefix <= to_prefix
    in_range = False
    for submission in sorted(submissions):
        name, _ = submission
        if name.upper() >= from_prefix and name.upper() <= sentinel:
            selected.append(submission)
    return selected


def join_columns(cols: List[Tuple[str, Path]]) -> List[Tuple[str, List[Path]]]:
    """Convert from [[("jon", P), ("mary", Q)], [("jon", R), ("mary, S)], ...]
    to [("jon", [P, R, ...]), ("mary", [Q, S ...]), ...]
    """
    merged = [(name, [path]) for name, path in cols[0]]
    for column in cols[1:]:
        merged_i = 0
        column_i = 0
        remerged = []  #
        # While more of both lists
        while merged_i < len(merged) and column_i < len(column):
            m_name, m_paths = merged[merged_i]
            c_name, c_path = column[column_i]
            if m_name == c_name:
                # Name components match; merge into result
                log.debug(f"Matched {m_name},{m_paths} to {c_name},{c_path}")
                m_paths.append(c_path)
                log.debug(f"Inserting {(m_name, m_paths)}")
                remerged.append((m_name, m_paths))
                merged_i += 1
                column_i += 1
            # Otherwise one or the other is missing
            elif m_name < c_name:
                # Missing element in column
                log.debug(f"No match for {m_name},{m_paths}")
                m_paths.append(None)
                log.debug(f"Inserting {m_name, m_paths}")
                remerged.append((m_name, m_paths))
                merged_i += 1
            elif c_name < m_name:
                # Missing element in first column ... this one is harder!
                log.debug(f"No match for {c_name}, {c_path}")
                paths = [None for p in m_paths]
                paths.append(c_path)
                log.debug(f"Inserting {c_name, paths}")
                remerged.append((c_name, paths))
                column_i += 1
            else:
                assert False, "Can't happen"
        # At end of at least one column
        # In case we have not reached end of all
        while merged_i < len(merged):
            m_name, m_paths = merged[merged_i]
            m_paths.append(None)
            log.debug(f"Appending from merged, {m_name, m_paths}")
            remerged.append((m_name, m_paths))
            merged_i += 1
        while column_i < len(column):
            c_name, c_path = column[column_i]
            _, sample_paths = merged[0]
            log.debug(f"Sample paths taken from first of {merged}")
            log.debug(f"With remerged {remerged}")
            # Note we have been appending to merged along the
            # way, so each row is one longer than the imaginary
            # row we imagine matching
            paths = [None for p in sample_paths[1:]]
            paths.append(c_path)
            log.debug(f"Appending from column, {c_name, paths}")
            remerged.append((c_name, paths))
            column_i += 1
        ## Ready for next column
        merged = remerged
        log.debug(f"Merged is now {merged}")
    return merged


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

def check_file(submission: Tuple[str, List[Path]],
               rename_to: List[str],
               grading_dir: str,
               test_name: str):
    # source_name = str(submission_path)
    # Execute in a temporary directory with copies
    # of support files
    tempdir = f"/tmp/{grading_dir}"
    shutil.rmtree(tempdir, ignore_errors=True)
    shutil.copytree(grading_dir, tempdir)
    student, files = submission
    for i in range(len(files)):
        source_name = files[i]
        canon_name = rename_to[i]
        if not source_name:
            continue
        dest_name = f"{tempdir}/{canon_name}"
        shutil.copy(source_name, dest_name)
    test_name = f"{tempdir}/{test_name}"
    try:
        execution = subprocess.run(["python3", test_name, "-v"],
                               cwd=tempdir,
                               capture_output=True,
                               timeout=5)
        print(f"Return code: {execution.returncode}")
        stderr = str(execution.stderr, 'utf-8', 'ignore')
        print(f"Stderr: \n{stderr}")
    except Exception as e:
        print(f"Interrupted:  {e}")

def excerpt(path: Path, units: List[str]):
    """Print excerpts of submitted code for listed units
    (class and function names)
    """
    # We are looking for any of these names, as functions or classes
    units_disjunct = "|".join(units)

    # A class, function, or method definition is the first
    # thing on a line.  It begins with "class" or "def", then
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

    # Sometimes we want many methods with the same name, so it is
    # useful to also record the last class name encountered
    any_class_re = f"""
    ^(?P<indent>\\s*)             # Only indentation before it
         (?P<kind> class)\\s+   # A class  
         (?P<unit> \w+)         # with this name
         \\W.*"""                 # Followed by anything
    any_class_pat = re.compile(any_class_re, re.VERBOSE)

    recent_class = "NO CLASS"
    try:
        f = open(path)
        line_num = 0
        lines = iter(f)  # Allows CHUNKED for loops
        for line in lines:
            line_num += 1
            log.debug(f"Scanning line {line.rstrip()}")
            found = start_pat.match(line)
            if found:
                fields = found.groupdict()
                log.debug(f"Starting unit '{found.groups()}'")
                log.debug(f"Fields: '{fields}'")
                indent = len(fields["indent"])
                # If it looks like a function, but is indented, we'll print
                # the class it appears to belong to.  If it looks like a class,
                # we'll remember that in case we need it later
                # Link to original text
                print(f"at {path}:{line_num}")
                if fields["kind"] == "def" and indent > 0:
                    print(f"in class '{recent_class}':")
                elif fields["kind"] == "class":
                    recent_class = fields["unit"]

                print(line.rstrip())  # Unit header line for class or function

                # Subsequent lines:  Continue as long as they are indented to
                # indicate inclusion in the current unit.
                for more in lines:
                    line_num += 1
                    is_a_unit = next_unit.match(more)

                    # Stop excerpting at dedent that is
                    # not a comment and not a new unit
                    if ((is_a_unit is None)
                        and len(more.lstrip()) > 0
                        and more.lstrip()[0] != "#"
                        and  len(more) - len(more.lstrip()) <= indent):
                        break

                    #  Still within the same unit ... print and go on.
                    if not is_a_unit:
                        print(more.rstrip())
                        continue

                    # We've hit another unit. If it is indented
                    # within this one, we just continue
                    log.debug(f"Next unit '{is_a_unit.groups()}'")
                    fields = is_a_unit.groupdict()
                    if fields["indent"]:
                        unit_indent = len(fields["indent"])
                        if unit_indent > indent:
                            print(more.rstrip())
                            continue
                    # If it's a class, we take note whether or not
                    # we are interested, because it might contain
                    # something we are interested in.
                    if fields["kind"] == "class":
                        recent_class = fields["unit"]
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
            else:
                # Outside a unit of interest, but we take note of
                # classes that might *contain* units of interest.
                is_a_class = any_class_pat.match(line)
                if is_a_class:
                    recent_class = is_a_class.groupdict()["unit"]
        
    except Exception as e:
        print("*** Exception while trying to excerpt")
        print(e)


def main():
    try:
        config = configure("grader.ini")
        problem = config["DEFAULT"]["select"]
        name_globs = config[problem]["glob"].split(",")
        canonical_names = config[problem]["canon"].split(",")
        subdir = config[problem]["dir"]
        units = config[problem]["excerpt_units"]
        test_name = config[problem]["tests"]
        if "submissions_dir" in config[problem]:
            dir = config[problem]["submissions_dir"]
        else:
            dir = "submissions"
        if "submissions_from" in config[problem]:
            submissions_from = config[problem]["submissions_from"]
            submissions_to = config[problem]["submissions_to"]
        else:
            submissions_from = None
            submissions_to = None
    except KeyError as e:
        log.warning(f"{e}\nMissing entry in grader.ini")
        sys.exit(8)

    print(f"\nProblem: {name_globs} ({canonical_names})")
    # name_table = roster_munge.read_table() # Now in submissions_for_problem
    submissions = submissions_for_problem(name_globs, dir)
    assert submissions, f"No match for {name_globs} in {dir}"
    if submissions_from:
        submissions = select_submissions(submissions, submissions_from, submissions_to)
        assert submissions, f"No submissions in range {submissions_from}..{submissions_to}"
    for submission in submissions:
        # name = extract_student_name(submission, name_table)
        name, files = submission
        print("\n-----------------------------------------")
        print(f"{name} => \t{submission} (BEGIN)")
        # The following creates clickable file link in PyCharm run window
        # print(f"{name} => \nat {submission}:0 (BEGIN)")
        check_file(submission, canonical_names, subdir, test_name)
        print()
        for file in files:
            if file:
                excerpt(file, units.split(","))
            else:
                print(f"Missing file for {name}")
        print(f"/ {name} (END)")
        # break # DEBUG - Testing just on first entry for each


if __name__ == "__main__":
    main()




