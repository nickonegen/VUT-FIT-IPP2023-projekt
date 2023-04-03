"""
Triedy pre ovládanie toku interprétu jazyka IPPcode23.
@author: Onegen Something <xonege99@vutbr.cz>
"""


class Frame:
    """Trieda reprezentujúca dátový rámec združujúci premenné"""

    def __init__(self):
        self._variables = {}

    def __repr__(self):
        if self.size() == 0:
            return ""

        rstr = "\n".join(f"    {k} = {repr(v)}" for k, v in self._variables.items())
        return f"{rstr}\n"

    def size(self):
        """Získa počet premenných v rámci"""
        return len(self._variables)

    def has_variable(self, name):
        """Dotaz na existenciu premennej v rámci"""
        return name in self._variables

    def get_variable(self, name):
        """Získa hodnotu premennej s daným názvom (neexistuje -> ENOVAR)"""
        if self.has_variable(name):
            return self._variables[name]
        raise KeyError(f"Couldn't access non-existant variable {name}")

    def define_variable(self, name):
        """Deklaruje novú premennú v rámci (redeklarácia -> ESEM)"""
        if not self.has_variable(name):
            self._variables[name] = None
        else:
            raise RuntimeError(f"Redefinition of variable {name}")

    def set_variable(self, name, value):
        """Nastaví hodnotu premennej v rámci (neexistuje -> ENOVAR)"""
        if self.has_variable(name):
            self._variables[name] = value
        else:
            raise KeyError(f"Couldn't set non-existant variable {name}")

    def delete_variable(self, name):
        """Odstráni premennú z rámca (neexistuje -> ENOVAR)"""
        if self.has_variable(name):
            del self._variables[name]
        else:
            raise KeyError(f"Couldn't delete non-existant variable {name}")


class Instruction:
    """
    Trieda reprezentujúca inštrukciu jazyka IPPcode23

    Atribúty:
        opcode (str): kód inštrukcie
        operands (Value|UnresolvedVariable): zoznam operandov
    """

    def __init__(self, opcode, operands):
        self.opcode = opcode
        self.operands = operands

    def __repr__(self):
        operands = " ".join([repr(operand) for operand in self.operands])
        return f"{self.opcode} {operands}"

    def replace_operand(self, index, value):
        """Nahradí operand inštrukcie na danom indexe"""
        self.operands[index] = value

    def next_unresolved(self):
        """Získa index ďalšieho nedefinovaného operandu (žiadny -> -1)"""
        for index, operand in enumerate(self.operands):
            if isinstance(operand, UnresolvedVariable):
                return index
        return -1


class Value:
    """
    Trieda pre reprezentáciu hodnoty v IPPcode23.

    Atribúty:
        type (str): typ hodnoty
        value (any): hodnota

    Vyvolá:
        TypeError: pokiaľ je hodnota a typ nekompatibilné
    """

    def __init__(self, value_type, value_raw):
        self.type = value_type
        match value_type:
            case "int":
                self.content = int(value_raw)
            case "bool":
                self.content = bool(value_raw)
            case "string":
                self.content = str(value_raw)
            case "float":
                self.content = float(value_raw)
            case "type":
                self.content = str(value_raw)
            case "nil":
                self.content = None
            case _:
                raise TypeError(f"Invalid value type: {value_type}")

    def __repr__(self):
        return f"{self.type}@{self.content}"

    def __str__(self):
        match self.type:
            case "bool":
                return str(self.content).lower()
            case "nil":
                return ""
            case _:
                return str(self.content)


class UnresolvedVariable:
    """
    Trieda reprezentujúca premennú v argumente inštrukcie, ktorej je
    nutné počas interpretácie získať hodnotu (rieši execute_next())

    Atribúty:
        varid (str): IPPcode23 premenná (formát xF@id)

    Vyvolá:
        RuntimeError: pokiaľ je formát argumentu neplatný
    """

    def __init__(self, arg):
        self.frame, self.name = arg.split("@", maxsplit=1)
        if self.frame.upper() not in ("GF", "LF", "TF"):
            raise RuntimeError(f"Invalid variable name: {arg}")

    def __repr__(self):
        return f"{self.frame}@{self.name}"


class LabelArg:
    """Trieda reprezentujúca náveštie v skokovej inštrukcií"""

    def __init__(self, label):
        self.label = label

    def __repr__(self):
        return f"{self.label}"
