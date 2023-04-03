"""
IPP projekt 2023, časť 2

Interprét XML reprezentácie programu v jazyku IPPcode23
@author: Onegen Something <xonege99@vutbr.cz>
"""

import sys, getopt

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
    "source": None,
    "input": None,
    "stats": False,
    "verbose": False,
    "fancy": False,
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

try:
    opts, args = getopt.getopt(sys.argv[1:], "hvf", ["help", "source=", "input="])
except getopt.GetoptError as err:
    throw_err("EPARAM", str(err))
    sys.exit(RETCODE.get("EPARAM"))

for opt, arg in opts:
    if opt in ("-h", "--help"):
        print_help()
    elif opt == "--source":
        ginfo["source"] = arg
    elif opt == "--input":
        ginfo["input"] = arg
    elif opt == "-v":
        ginfo["verbose"] = True
    elif opt == "-f":
        ginfo["fancy"] = True

throw_err("EINT", "Not implemented yet")
