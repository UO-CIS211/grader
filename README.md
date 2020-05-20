# Grader script for Python coding exams in Canvas


This script is designed to test and excerpt a batch of Python programs downloaded from Canvas.  It was designed initially for exams in CIS 211 at U. Oregon in winter and spring 2020, but might be adapted for other coursework in computer science. 

The current version of `grader.py` is specific to 
Python version 3 and the `unittest` testing framework. 
It is likely that it could be generalized, but I don't
want to do so until I have a specific use case to guide 
the work.  Contact me (michal@cs.uoregon.edu) if you 
are interested in working with me on making it work 
for program submissions in other programming languages. 

`grader.py` is designed for use with the SpeedGrader feature of Canvas to grade file uploads containing program source code. It might conceivably be made to work with another LMS, but not trivially, because it relies on details like the way Canvas 
mooshes student name and file name into a file name. 
Some parts of this script might be usable in a grading 
script adapted to another LMS. 

`grader.py` assumes you want to run student code with a test suite, and that you also want to *read the code*, or at least an excerpt of the code.  If you want to grade student programs automatically without actually looking at their code, this is probably not the script for you. 

## What it does 

The script expects to find a subdirectory
called `submissions` containing code submitted by students.  These could be files uploaded in response to multiple problems, as is the case when grading a 
CIS 211 exam.  Within the submissions directory as 
provided by Canvas, the name of each submitted file is a mashup of student name, submitted file name, and various deeply secrete numbers.  The script, 
under control of a configuration file,  is designed to select submissions for one particular problem at a time by matching part of the file name. It copies the each matching submission to a subdirectory where it expects to find a test suite. In that subdirectory it executes the test suite and gathers output.  It also scans the submission to produce an excerpt for inspection.  Output and exerpts, along with identifying information, and concatenated together in the output, which is designed to be read while using the 'speedgrader' feature of Canvas. 

## Setup

`submissions` (expanded from a zip file downloaded from Canvas) should be installed as a subdirectory.  Additionally, there should be a subdirectory for each 
problem to be graded (e.g., "q1", "q2", etc for an exam).  The problem subdirectories will be the working directories for testing student submissions.  A test suite should be located in each problem subdirectory. 

Edit `grader.ini` to control `grader.py` (next section). 

## Configuration 

`grader.py` is controlled and configured by `grader.ini`, which looks like this: 

```
[DEFAULT]
select = Q3
[Q1]
glob : q1_interval       # select submission 
canon : q1_intervals.py  # Rename submission
dir : q1                 # problem directory
excerpt_from : class Interval   
excerpt_to: NONE    
[Q2]
glob : q2_color
canon : q2_color_tiles.py
dir : q2
excerpt_from : class Color
excerpt_to: def main()
[Q3]
glob : q3_shapes
canon: q3_shapes.py
dir: q3
excerpt_from : class Shape
excerpt_to : NONE
```

Note that `grader.py` permits line-ending comments, 
contrary to typical `.ini` file formats.  

In the `[DEFAULT]` section, key `select` determines the 
section that the remainder of the configuration will 
be drawn from.  In the example, problem `Q3` is selected, so the remainder of the configuration will 
be drawn from section `[Q3]`.  This is because I 
normally grade all submissions for a given problem 
before moving on to the next problem, rather than 
grading all problems for a given student.  

`glob` is a pattern to match student submissions for a given problem.  It is a Unix file-glob pattern, so for 
example `f1*.py` matches `smith_will_f1ghter_pilot.py_18345` 
as well as `norris_peter_f123.py_28238`.  It is best to give a `glob` pattern that is general enough to tolerate some variation in the file names that students give, even when they do not follow directions precisely. 

`canon` is a canonical name that the submitted file will be given in the working directory. Typically the test suite will refer to the student code by this name, so the renaming also helps cope with minor discrepancies in file names provided by students. 

`dir` is the working directory for a particular problem, i.e., where the test suite will be found and where the canonically named student submission will be placed. 

`excerpt_from` and `excerpt_to` are patterns designed to match lines in the submitted source code.  Lines between those matches, but not including the `excerpt_to` match, will be included in the grader output.   If you desire to read code to the end of the submitted file, as a special case `NONE` can be specified as the `excerpt_to` pattern.  Note that 
patterns may contain spaces but should not contain 
`#`, which would be treated as a comment in the `.ini` 
file. 


# Output

The output will be a sequence of results in alphabetical order by student surname.  Each set of 
results will include identifying information, 
test results, and code excerpt.  

## Identifying information 

The first part of test results for a student look 
like this: 

```
-----------------------------------------
lastname, firstname => 	submissions/lastname_firstname93966_question_2053772_8680838_q1_tree_height.py
```

If a student has a multi-part surname, like *de la rossa*, the script may mistake parts of the surname for a given name. 

## Test results 

The identifying information is followed by the output of the test suite.  Typically it will look like this:

```
Return code: 0
Stderr: ....
----------------------------------------------------------------------
Ran 4 tests in 0.001s

OK
```

Sometimes, however, it may look like this: 

```
Interrupted:  Command '['python3', 'q1/test_q1.py']' timed out after 3 seconds
```

or like this 

```
----------------------------------------------------------------------
Traceback (most recent call last):
  File "q1/test_q1.py", line 31, in test_4_skew_right
    self.assertEqual(tree.min_height(), 2)
  File "/Users/michal/Dropbox/20S-211/exams/midterm2-s20/grader/q1/q1_tree_height.py", line 44, in min_height
    return min(self._left.min_height() +1)
  File "/Users/michal/Dropbox/20S-211/exams/midterm2-s20/grader/q1/q1_tree_height.py", line 44, in min_height
    return min(self._left.min_height() +1)
TypeError: 'int' object is not iterable

----------------------------------------------------------------------
Ran 4 tests in 0.001s

FAILED (errors=3)
```

(I have truncated the error report in the last example.  
The full list of test failures, and stack traces if any, are included.) 

## Code Excerpt

After the test results, an excerpt of the code (as specifed by the `excerpt_from` and `excerpt_to` configuration variables) is printed.  

# Future Work 

Several enhancements of `grader.py` are possible. Here are some currently planned or under consideration: 

* Excerpt multiple sections of source code

* Do a better job of parsing multi-part student names

* Run in a Docker container to protect against malicious student submissions

* Make timeout configurable

* Make test program name configurable

* Allow multiple test programs

* More flexible configuration of the test invocation, not specific to Python 3 on Mac OS X. 

Other fixes and enhancements are possible ... contact 
michal@cs.uoregon.edu
