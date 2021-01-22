# Marking

## Mark components

Marks come from up to four sources:

* Autograded OKpy tests.
* `#M:` annotations added by the marker.
* Hand-graded plot questions.
* Hand-graded text questions.

The total marks are the total of the marks from these four sources.

## Autograded OKpy tests

Autograded tegsts are in [OKpy
format](https://okpy.github.io/documentation/client.html#ok-client-setup-ok-tests)

We run the tests by having test cells in the notebook, and putting suitable
tests in the `test` directory, and executing all the code in the notebook.

The tests are in the form of test cells in the notebook:

```python
_ = ok.grade('q_01_a_value')
```

This is a code cell that runs a series of tests on variables defined in the
notebook.

The tests are in a `tests` subdirectory in Python files, of [format defined
here](https://okpy.github.io/documentation/client.html#ok-client-setup-ok-tests).
For example, in the case, the test would be in the file
`tests/q_01_a_value.py`.

The test might check the value of the variable `a` in the
notebook.  It will give output a bit like this:

```
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Running tests

---------------------------------------------------------------------
Test summary
    Passed: 4
    Failed: 0
[ooooooooook] 100.0% passed
```

In this case the tests for this question have passed, and the students gets
full marks for the question.

Or, the output might look like this:

```
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Running tests

---------------------------------------------------------------------
Question q_01_a_value > Suite 1 > Case 4

>>> # Value for a should be 43
>>> a == 42
False

# Error: expected
#     True
# but got
#     False

Run only this test case with "python3 ok -q q_01_a_value --suite 1 --case 4"
---------------------------------------------------------------------
Test summary
    Passed: 3
    Failed: 1
[oooooook...] 75.0% passed
```

In this case the last of 4 checks failed, and the student gets *no marks* for
the question.  The first few tests are always general, ball-park tests to test
if a value is defined, and whether it is of the right type - such as integer,
or an array.  The last one or two checks test if the value is correct - hence
the value has to pass all checks to give the marks.

For MCPMark output, you will find the details of the marks for each autograded
question in a file `component/<component name>/marking/autograde.md`.

## M: annotations

The marker can add or subtract marks by adding lines in the notebook of form:

```python
#M: 5
```

This would add 5 to the eventual marks for the notebook.

We use this in various situations.

If any cell causes the notebook to raise an error and stop execution, then we
usually add an annotation to subtract 5% of the total marks for the notebook.
For example, if the total marks for the notebook were 50, then we add:

```python
#Marking: this cell causes an error
#M: 2.5
```

We will also edit or comment out the code causing the error in order to allow
the notebook to run.

If the cell causing the error defines a value used in the test, then we adjust
the error penalty, in the following way.  Let P be the marks giving 5% of the
notebook total - 2.5 in the example above.  Let Q be the marks for the test for
this cell.  The marks we subtract are the minimum of (Q-P, 0).  For example, if
the question answered in this cell gives 2 marks, and P=2.5 (as above), then we
subtract 0.5:

```python
#M: -0.5
```

Another use of the `#M:` markup is for fixing cells that cause errors further
down the notebook.  In such as case we use the `#M:` markup to drop the marks
for the incorrect cell, and then fix the cell to prevent further errors in
cells below that.  For example consider the following sequence of cells and
tests in a student submission:

~~~
```{python}
# This is a code cell
# Define variable a to have the value 42
# 5 marks.
a = 30
```

```python
_ = ok.grade('q_01_a_value')
```

```{python}
# This is another code cell
# Define variable b to be a plus 10
# 5 marks.
b = a + 10
```

```python
_ = ok.grade('q_02_b_value')
```
~~~

In this case the first cell is incorrect, and the student should lose 5 marks,
but the second cell is correct, and the student should get 5 marks.  But, as it
stands, the student will lose marks for both cells.

We the markers will try to detect sequences like these and edit them so the
student does not get penalized twice for a single error, like this:

~~~
```{python}
# This is a code cell
# Define variable a to have the value 42
# 5 marks.
#Marking: dock the marks for this question, and fix.
#M: -5
# a = 30
a = 42
```

```python
_ = ok.grade('q_01_a_value')
```

```{python}
# This is another code cell
# Define variable b to be a plus 10
# 5 marks.
b = a + 10
```

```python
_ = ok.grade('q_02_b_value')
```
~~~

# Hand-graded plot questions.

The MCPMark system can automatically execute student notebooks, and extract
generated plots into a single plot-only notebook that contains all the plots
for each student notebook.  The marker then goes through this single notebook
and allocates marks for each plot question in the notebook, for each student.

The plot-only notebook, with manual grades, should be in
`components/<component_name>/marking/plot_nbs.ipynb`.

Usually the marker also writes a file giving the criteria for the marks for
each plot.

Some notebook assignments have no graded plot questions.

# Hand-graded text questions.

Some questions are free text, and ask the student to explain something or give
justification for an answer.

The MCPMark system extracts the text for these questions into a single text
file for each manual question.  For example, if the text question has name
`my_text_question`, then the extracted text for all such questions, across
student notebooks, would be
`components/<component_name>/marking/my_text_question_report.md`.

The marker edits this file to record marks for each student.

As for the plot questions, the marker normally writes a file giving criteria
for marks on the text questions.
