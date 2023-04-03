"""
IPP projekt 2023, časť 2

Interprét XML reprezentácie programu v jazyku IPPcode23
@author: Onegen Something <xonege99@vutbr.cz>
"""

import sys
import getopt
import xml.etree.ElementTree as ET  # skipcq: BAN-B405
from lib_interpret.ippc_interpreter import Interpreter

"""
Konštanty a globálne premenné
    @const RETCODE: kódy návratových hodnôt
    @var ginfo: globálne informácie o programovom behu
"""

RETCODE = {
    # Celo-projektové návratové hodnoty
    "OK": 0,
    "EPARAM": 10,  # Chybné parametre
    "ENOENT": 11,  # Chyba pri otváraní súboru
    "EWRITE": 12,  # Chyba pri zápise
    "EINT": 99,  # Interná chyba
    # Chyby spracovania XML
    "EXML": 31,  # Chyba XML formátovania
    "ESTRUC": 32,  # Chybná štruktúra XML
    # Chyby interpretácie
    "ESEM": 52,  # Semantická chyba
    "EOTYPE": 53,  # Nepovolený typ operandu
    "ENOVAR": 54,  # Prístup k neexistujúcej premennej
    "ENOFRM": 55,  # Prístup k neexistujúcemu rámcu
    "ENOVAL": 56,  # Chýbajúca hodnota
    "EBADVL": 57,  # Chybná hodnota
    "ESTR": 58,  # Nesprávne zaobchádzanie s reťazcom
}

ginfo = {
    "source": None,  # Zdrojový súbor
    "input": None,  # Vstupný súbor
    "stats": False,  # Štatistiky (STATI, zatiaľ nepoužité)
    "verbose": False,  # Rozšírený výpis interpretácie
    "fancy": False,  # Krajší výpis
}

"""
Pomocné funkcie
    @func print_error(str, str): vypíše chybovú hlášku na stderr
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


def throw_err(ecode, msg, instr=None):
    COLORED = ginfo.get("fancy", False)

    err_prefix = "ERR!"
    code_label = "code"
    instr_label = "instr"

    if COLORED:
        err_prefix = "\033[31;49;1mERR!\033[0m"
        code_label = "\033[35;49mcode\033[0m"
        instr_label = "\033[35;49minstr\033[0m"

    err_str = f"{err_prefix} {code_label} {ecode}"

    if instr is not None:
        err_str += f"\n{instr_label} {instr}"

    err_str += f"\n{err_prefix} {msg}"
    print(err_str, file=sys.stderr)

    sys.exit(RETCODE.get(ecode))


"""
Spúšťacie parametre
"""

source_file = None
input_file = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "hvf", ["help", "source=", "input="])
except getopt.GetoptError as error:
    throw_err("EPARAM", str(error))
    sys.exit(RETCODE.get("EPARAM"))

for opt, arg in opts:
    if opt in ("--help", "-h"):
        print_help()
    elif opt == "--source":
        source_file = arg
    elif opt == "--input":
        input_file = arg
    elif opt == "-v":
        ginfo["verbose"] = True
    elif opt == "-f":
        ginfo["fancy"] = True

if source_file is None and input_file is None:
    throw_err("EPARAM", "--source or --input required")

if source_file is None:
    ginfo["source"] = sys.stdin.read()
else:
    with open(source_file, "r") as f:
        ginfo["source"] = f.read()

if input_file is None:
    ginfo["input"] = sys.stdin.read()
else:
    with open(input_file, "r") as f:
        ginfo["input"] = f.read()

try:
    interpret = Interpreter(ginfo.get("source"))
except ET.ParseError as error:
    throw_err("EXML", str(error))
    sys.exit(RETCODE.get("EXML"))
except Exception as error:
    throw_err("ESTRUC", error.args[0])
    sys.exit(RETCODE.get("ESTRUC"))


print(interpret)

throw_err("EINT", "Not implemented yet")
