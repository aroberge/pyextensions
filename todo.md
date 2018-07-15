# todo

## IMPORTANT

- [ ] Put the console in a separate subproject. Have all extra "nice" features (colouring of output, excepthook, etc.) only added in this subproject. This should help to simplify significantly the main project.
- [ ] Fix traceback in console so that correct syntax error is picked up.
- [x] Implement proper repeat handling transformation with limitations on syntax allowed for repeat loop
- [ ] Consider implementing "simplified Python" (Snakelet?) with repeat loops and limited syntax e.g. all paren or brackets must close on a single line; no semi-colon allowed as tokens, etc.
    - [ ]  See if it would not be possible to use a hook to analyze code line by line prior to executing it, thus catching syntax early. If so, use this analyzer in the console.
    - [ ] Consider implementing a "simplified French Python" (Serpenteau?)
- [ ] Implement an excepthook to provide simplified tracebacks - perhaps with a French translation.
- [ ] Keep track of required transformers on a file by file basis. For console, use filename '<console>'.  Add test where a .notpy imports another .notpy with different transformations needed - but some that conflict (for example, replacing a string by another one.)
- [ ] Add note about repeated calls to a given transformer are possible by including its name more than once on the #ext line.

 

Note: do not use gettext. 


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
- [ ] Idea: register codec and do codec transformations?   Or, perhaps reproduce the pyxl (https://github.com/dropbox/pyxl) with a source transformation.
- [ ] Allow multiple extensions to be specified? This would enable using multiple "tranformer libraries" imported from pipy.


## Idea for 'hello world' of bytecode transformation.

Do a "confused math" transformation, interchanging BINARY_ADD and BINARY_MULTIPLY.   To have the code more portable for different cPython versions use

    import dis
    add = dis.opmap[BINARY_ADD]
    mult = dis.opmap[BINARY_MULTIPLY]

The problem I have is finding out where and how to use this information to transform the code.

Of course, a slightly longer example that does not simply involve replacements of one Bytecode instruction by another one would be something useful to have.