"""
In the following explanation, when we mention "the console" we refer to
a session using the pyextensions interactive console included in this package.

Possible invocations of this module:

1. python -m pyextensions: we want to start the console
2. python -m pyextensions script: we want to run "script" as the main program
                                but do not want to start the console
3. python -i -m pyextensions script: we want to run "script" as the main program
                                and we do want to start the console after
                                script has ended
4. python -m pyextensions trans1 trans2 script: we want to run "script" as the
                                main program, after registering the
                                tansformers "trans1" and "trans2";
                                we do not want to start the console
5. python -i -m pyextensions trans1 trans2 script: same as 4 except that we
                                want to start the console when script ends

Note that a console is started in all cases except 4 above.
"""
import argparse
import sys
import os.path
from . import console, import_hook, transforms

# It is assumed that code transformers are third-party modules
# to be installed in a location from where they can be imported.
# For this proof of concept, we add a fake site-packages directory
# where the sample transformers will be located

top_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
fake_site_pkg = os.path.join(top_dir, "fake_site_pkg")

if not os.path.exists(fake_site_pkg):
    raise NotImplementedError(
        "A fake_site_pkg directory must exist for this demo to work correctly."
    )
sys.path.insert(0, fake_site_pkg)


if "-m" in sys.argv: 
    parser = argparse.ArgumentParser(description="Description to be added.")
    parser.add_argument(
        "-s",
        "--source",
        help="""Source file to be transformed. 
                Format: path.to.file -- Do not include an extension.""",
    )
    parser.add_argument(
        "-x",
        "--file_extension",
        help="The file extension of the module to load; default=notpy")

    parser.add_argument(
        "-c",
        "--convert",
        help="Show the code transformed into standard Python.",
        action='store_true')

    args = parser.parse_args()

    if args.convert:
        show_python = True
        import_hook.CONVERT = True
    else:
        show_python = False

    if args.file_extension is not None:
        import_hook.FILE_EXT = args.file_extension

    if args.source is not None:
        try:
            main_module = import_hook.import_main(args.source)
            if sys.flags.interactive:
                main_dict = {}
                for var in dir(main_module):
                    if var in ["__cached__", "__loader__", "__package__", "__spec__"]:
                        continue
                    main_dict[var] = getattr(main_module, var)
                console.start_console(local_vars=main_dict, show_python=show_python)
        except ModuleNotFoundError:
            print("Could not find module ", args.source, "\n")
            raise
    else:
        console.start_console(local_vars=None, show_python=show_python)

