"""Translate Duckweb roster in CSV format
to table mapping Canvas munged names to
complete names as given in Duckweb.

Example:
"Baker-Rozell, Charles W" => "bakerrozellcharles"
"Bermudez Antonino, Jan H" => "bermudezantoninojan"

We pick up *one* name beyond the comma and
compress out punctuation and spaces before it.
"""

import csv
from typing import Dict
import configparser

NAME_CRUSH = str.maketrans("", "", "-_' ")  # To crush from Canvas as well as Roster
def munge_name(s: str) -> str:
    """Canvas submission student name from Duckweb roster name.
    Examples:
    "Baker-Rozell, Charles W" => "bakerrozellcharles"
    "Bermudez Antonino, Jan H" => "bermudezantoninojan"
    """
    surname, given = s.split(", ")
    # Discard middle initial if any
    given = given.split(" ")[0]
    # Lower case without spaces of punctuation
    surname = surname.lower().translate(NAME_CRUSH)
    given = given.lower().translate(NAME_CRUSH)
    return surname + given

def create_table(roster: csv.reader) -> Dict[str, str]:
    """Converts roster in CSV form to map: Canvas name -> roster name"""
    table = dict()
    # Roster table is not at top, so we will hard-code
    # the columns and look for students
    rows = iter(roster)
    for row in rows:
        if len(row) > 1 and row[1] == "UO ID":
            assert row[0] == "Student name"
            break
    else:
        raise LookupError("Couldn't find roster part")
    # Iterator is now advanced past header
    for row in rows:
        if len(row) < 5:
            break
        roster_name = row[0]
        canvas_name = munge_name(roster_name)
        table[canvas_name] = roster_name
    return table

def smoke():
    """Smoke test"""
    example = "Baker-Rozell, Charles W"
    expect = "bakerrozellcharles"
    result = munge_name(example)
    assert result == expect

    example = "Bermudez Antonino, Jan H"
    expect = "bermudezantoninojan"
    result = munge_name(example)
    assert result == expect

def configure(filename: str) -> configparser.ConfigParser:
    """The returned object is something like a dict;
    see configparser documentation for access
    instructions
    """
    conf = configparser.ConfigParser(inline_comment_prefixes="#")
    conf.read_file(open(filename))
    return conf

def read_table():
    config = configure("grader.ini")
    roster_csv = open(config["DEFAULT"]["roster"])
    roster_reader = csv.reader(roster_csv)
    table = create_table(roster_reader)
    return table

def main():
    table = read_table()
    for key in table:
        value = table[key]
        print(f'{key:20}\t"{value}"')


if __name__ == "__main__":
    main()
