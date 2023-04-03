"""
Triedy pre ovládanie toku interprétu jazyka IPPcode23.
@author: Onegen Something <xonege99@vutbr.cz>
"""

from lib_interpret.ippc_idata import Stack, Value


class Frame:
    """
    Trieda reprezentujúca dátový rámec združujúci premenné.

    Atribúty:
        _variables (dict): slovník premenných
    """

    def __init__(self):
        self._variables = {}

    def __repr__(self):
        if self.size() == 0:
            return ""
        return "\n".join([f"    {k} = {v}" for k, v in self._variables.items()]) + "\n"

    def size(self):
        """
        Vráti počet premenných v rámci.

        Vráti:
            int: počet premenných v rámci
        """
        return len(self._variables)

    def has_variable(self, name):
        """
        Dotaz na existenciu premennej v rámci.

        Argumenty:
            name (str): názov premennej

        Vráti:
            bool: true, ak sa premenná nachádza v rámci, inak false
        """
        return name in self._variables

    def get_variable(self, name):
        """
        Získa hodnotu premennej s daným názvom.

        Argumenty:
            name (str): názov premennej

        Vráti:
            Value: hodnota premennej

        Vyvolá:
            KeyError: pokiaľ sa premenná nenachádza v rámci
        """
        if self.has_variable(name):
            return self._variables[name]
        raise KeyError(f"Couldn't access non-existant variable {name}")

    def define_variable(self, name, value):
        """
        Definuje novú premennú v rámci.

        Argumenty:
            name (str): názov premennej
            value (Value): hodnota premennej

        Vyvolá:
            KeyError: pokiaľ sa premenná s daným názvom už nachádza v rámci
        """
        if not self.has_variable(name):
            self._variables[name] = value
        else:
            raise KeyError(f"Redefinition of variable {name}")

    def delete_variable(self, name):
        """
        Odstráni premennú z rámca (TODO: je toto vôbec potrebné?)

        Argumenty:
            name (str): názov premennej

        Vyvolá:
            KeyError: pokiaľ sa premenná nenachádza v rámci
        """
        if self.has_variable(name):
            del self._variables[name]
        else:
            raise KeyError(f"Couldn't delete non-existant variable {name}")


class Instruction:
    """
    Trieda reprezentujúca inštrukciu jazyka IPPcode23.

    Atribúty:
        opcode (str): kód inštrukcie
        operands (Value|UnresolvedVariable): zoznam operandov
    """

    def __init__(self, opcode, operands):
        self.opcode = opcode
        self.operands = operands

    def __repr__(self):
        operands = " ".join([str(operand) for operand in self.operands])
        return f"{self.opcode} {operands}"

    def replace_operand(self, index, value):
        """
        Nahradí operand inštrukcie.

        Argumenty:
            index (int): index operandu
            value (Value): nová hodnota operandu
        """
        self.operands[index] = value

    def next_unresolved(self):
        """
        Dotaz na existenciu premenných s nerozhodnutou hodnotou v inštrukcii.

        Vráti:
            int: index prvého nerozhodnutého operandu, alebo -1 pokiaľ
                inštrukcia takýto operand nemá
        """
        for index, operand in enumerate(self.operands):
            if isinstance(operand, UnresolvedVariable):
                return index
        return -1


class UnresolvedVariable:
    """
    Trieda reprezentujúca premennú v argumente inštrukcie, ktorá bude
    počas interpretácie nahradená jej hodnotou.

    Argumenty:
        varid (str): IPPcode23 premenná (formát xF@id)
    """

    def __init__(self, arg):
        self.frame, self.name = arg.split("@", maxsplit=1)
        if self.frame.upper() not in ("GF", "LF", "TF"):
            raise ValueError(f"Invalid variable name: {arg}")

    def __repr__(self):
        return f"{self.frame}@{self.name}"


class LabelArg:
    """
    Trieda reprezentujúca náveštie v skokovej inštrukcií

    Argumenty:
        label (str): náveštie
    """

    def __init__(self, label):
        self.label = label

    def __repr__(self):
        return f"{self.label}"
