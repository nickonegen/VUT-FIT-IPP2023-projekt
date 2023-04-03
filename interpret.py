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
    @func throw_err(str, str): vypíše chybovú hlášku na stderr a ukončí program
"""


def print_help():
    print("Usage: python3[.10] interpret.py [OPTIONS] <in out>")
    print("")
    print(" Interprets the XML representation of a IPPcode23 program.")
    print("")
    print("  --help              Prints this help message and exits.")
    print("  --source=<file>     Specifies the source file to be interpreted.")
    print("  --input=<file>      Specifies the input file to be used.")
    print("")
    print("   At least one of the options above must be specified.")
    print("   Aside from --help, the unspecified option of the two")
    print("   will be expected on standard input.")
    sys.exit(RETCODE.get("OK"))


def parse_args():
    arguments = {"source": None, "input": None}

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "source=", "input="])
    except getopt.GetoptError as error:
        throw_err("EPARAM", str(error))
        sys.exit(RETCODE["EPARAM"])

    for opt, arg in opts:
        if opt in ("--help", "-h"):
            print_help()
        elif opt == "--source":
            arguments["source"] = arg
        elif opt == "--input":
            arguments["input"] = arg

    if arguments["source"] is None and arguments["input"] is None:
        throw_err("EPARAM", "--source or --input required", arguments)

    return arguments


def throw_err(ecode, msg, instr=None):
    err_prefix = "\033[31;49;1mERR!\033[0m"
    code_label = "\033[35;49mcode\033[0m"
    instr_label = "\033[35;49minstr\033[0m"

    err_str = f"{err_prefix} {code_label} {ecode}"

    if instr is not None:
        err_str += f"\n{err_prefix} {instr_label} {instr}"

    err_str += f"\n{err_prefix} {msg}"
    print(err_str, file=sys.stderr)

    sys.exit(RETCODE.get(ecode))


"""
Hlavná časť programu
"""


def main():
    arguments = parse_args()

    try:
        arguments["source"] = (
            sys.stdin.read()
            if arguments["source"] is None
            else open(arguments["source"], "r").read()
        )
        arguments["input"] = (
            sys.stdin.read()
            if arguments["input"] is None
            else open(arguments["input"], "r").read()
        )
    except FileNotFoundError as error:
        throw_err("ENOENT", str(error))

    try:
        interpret = Interpreter(arguments.get("source"), arguments.get("input"))
    except ET.ParseError as error:
        throw_err("EXML", str(error))
        sys.exit(RETCODE.get("EXML"))
    except Exception as error:
        throw_err("ESTRUC", error.args[0])
        sys.exit(RETCODE.get("ESTRUC"))

    returncode = -1
    next_instruction = interpret.peek_instruction()
    while next_instruction is not None:
        try:
            returncode = interpret.execute_next()
            next_instruction = interpret.peek_instruction()
        except Exception as error:
            error_code = IEXCEPTIONC.get(type(error), "EINT")
            throw_err(error_code, error.args[0], next_instruction)

    print(interpret)
    sys.exit(returncode)


if __name__ == "__main__":
    main()
