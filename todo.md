# todo

## IMPORTANT

- [ ] Fix traceback in console so that correct syntax error is picked up.
- [x] Implement proper repeat handling transformation with limitations on syntax allowed for repeat loop
- [ ] Consider implementing "simplified Python" (Snakelet?) with repeat loops and limited syntax e.g. all paren or brackets must close on a single line; no semi-colon allowed as tokens, etc.
- [ ] Consider implementing a "simplified French Python" (Serpenteau?)
- [ ] Implement an excepthook to provide simplified tracebacks - perhaps with a French translation.

Note: do not use gettext. Too complicated for this project.


## Less important

- [x] use argparse for options
- [x] implement ast transformation with example
- [ ] implement bytecode transformation with example
- [x] ensure that transformations listed in source file are done in order
- [x] show transformed source in console
- [x] enable printing out transformed source
- [ ] enable saving transformed source to a file
- [ ] add python2 example 
- [ ] add loop example 
- [ ] add french syntax example 
- [ ] add loop_fr example 
- [X] add example with other file extension
- [X] create sphinx doc 
- [X] show on github pages
- [ ] add color option (warning, errors, transformed, foreground, background?) Perhaps have dedicated printing functions like print_error, print_warning, print_normal, print_transformed
- [ ] review https://www.python.org/doc/essays/cp4e/

