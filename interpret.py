"""
IPP projekt 2023, časť 2

Interprét XML reprezentácie programu v jazyku IPPcode23
@author: Onegen Something <xonege99@vutbr.cz>
"""

import sys
import getopt
import xml.etree.ElementTree as ET  # skipcq: BAN-B405
from lib_interpret.ippc_interpreter import Interpreter
from lib_interpret.ippc_idata import IEXCEPTIONC, RETCODE

"""
Pomocné funkcie
    @func print_help(): vypíše nápovedu na stdout a ukončí program
    @func parse_args(): spracuje argumenty programu
    @func read_file_content(str): načíta obsah súboru
    @func throw_err(str, str): vypíše chybovú hlášku na stderr a ukončí program
"""


def print_help():
    help_msg = (
        "Usage: python3[.10] interpret.py [OPTIONS] <in out>\n\n"
        " Interprets the XML representation of a IPPcode23 program.\n\n"
        "  --help              Prints this help message and exits.\n"
        "  --source=<file>     Specifies the source file to be interpreted.\n"
        "  --input=<file>      Specifies the input file to be used.\n\n"
        "   At least one of the options above must be specified.\n"
        "   Aside from --help, the unspecified option of the two\n"
        "   will be expected on standard input."
    )
    print(help_msg)
    sys.exit(RETCODE.get("OK"))


def parse_args():
    arguments = {"source": None, "input": None, "debug_print": False}

    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hd", ["help", "source=", "input="])
    except getopt.GetoptError as error:
        throw_err("EPARAM", str(error))
        sys.exit(RETCODE["EPARAM"])

    for opt, arg in opts:
        if opt in ("--help", "-h"):
            print_help()
        if opt == "-d":
            arguments["debug_print"] = True
        elif opt == "--source":
            arguments["source"] = arg  # type: ignore
        elif opt == "--input":
            arguments["input"] = arg  # type: ignore

    if arguments["source"] is None and arguments["input"] is None:
        throw_err("EPARAM", "--source or --input required")

    return arguments


def read_file_content(file_path):
    if file_path is None:
        try:
            return sys.stdin.read()
        except KeyboardInterrupt:
            throw_err("EINT", "Interrupted by user")
    try:
        with open(file_path, "r") as f:
            return f.read()
    except FileNotFoundError as error:
        throw_err("ENOENT", error.args[1])


def throw_err(ecode, msg, instr=None):
    err_prefix = "\033[31;49;1mERR!\033[0m"
    code_label = "\033[35;49mcode\033[0m"
    instr_label = "\033[35;49minstr\033[0m"
    err_msg = str(msg).replace('"', "").replace("'", "")

    err_str = f"{err_prefix} {code_label} {ecode}"
    if instr is not None:
        err_str += f"\n{err_prefix} {instr_label} {instr}"
    err_str += f"\n{err_prefix} {err_msg}"

    print(err_str, file=sys.stderr)
    sys.exit(RETCODE.get(ecode))


"""
Hlavná časť programu
"""


def main():
    arguments = parse_args()
    source_cont = read_file_content(arguments["source"])
    input_cont = read_file_content(arguments["input"])

    try:
        interpret = Interpreter(source_cont, input_cont)
    except ET.ParseError as error:
        throw_err("EXML", str(error))
        sys.exit(RETCODE.get("EXML"))
    except KeyboardInterrupt:
        throw_err("EINT", "Interrupted by user")
        sys.exit(RETCODE.get("EINT"))
    except Exception as error:  # skipcq: PYL-W0703 - catch all exceptions
        throw_err("ESTRUC", str(error))
        sys.exit(RETCODE.get("ESTRUC"))

    if arguments["debug_print"]:
        interpret.make_verbose()

    returncode = 0
    while True:
        next_instruction = interpret.peek_instruction()
        if next_instruction is None:
            break

        try:
            returncode = interpret.execute_next()
        except KeyboardInterrupt:
            throw_err("EINT", "Interrupted by user")
        except Exception as error:  # skipcq: PYL-W0703 - catch all exceptions
            error_code = IEXCEPTIONC.get(type(error), "EINT")  # type: ignore
            throw_err(error_code, str(error), next_instruction)

    sys.exit(returncode)


if __name__ == "__main__":
    main()
