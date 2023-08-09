# Matrix Lantern Style Guide

This guide will help you in understanding the coding style being used in this project. Please adhere to these rules when contributing to the project for better readability and understanding of the code.


## Indentation

Use tabs for indentation. The code uses one tab per indentation level.


## Functions

Use lower case words separated by underscores. Function names should be descriptive of their function.

```
def my_function():
	pass
```


## Variables

Similar to function names, variable names should also be lowercase with words separated by underscores. They should be descriptive.

```
# good
my_variable = 10

# bad
mv = 10
```


## Commenting

Inline comments should be used sparingly. The use of comments is to clarify complex sections of code. If your code is straightforward, there's no need for comments.

```
# Good
def complex_algorithm():
	# This line does this...
	complex_line_of_code_here

# Bad
def simple_algorithm():
	# This line increments by 1
	counter += 1
```


## Function Calls

Function calls and definitions should have no space between the function name and the parentheses.

```
# Good
print("Hello, World!")

# Bad
print ("Hello, World!")
```


## Constants

Use uppercase with underscores to declare constants.

```
# Good
CONSTANT_NAME = 'Hello, World!'

# Bad
Constant_name = 'Hello, World!'
constantName = 'Hello, World!'
```


## Default Function Arguments

When using default arguments, there should be no spaces around the equals sign.

```
# Good
def my_func(default_arg='default'):

# Bad
def my_func(default_arg = 'default'):
```
