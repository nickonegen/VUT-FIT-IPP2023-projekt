"""
Triedy pre ovládanie toku interprétu jazyka IPPcode23.
@author: Onegen Something <xonege99@vutbr.cz>
"""

import re


class Value:
    """
    Trieda pre reprezentáciu hodnoty v IPPcode23.

    Atribúty:
        type (str): typ hodnoty
        value (any): hodnota

    Vyvolá:
        TypeError: pokiaľ je hodnota a typ nekompatibilné
    """

    def __init__(self, value_type: str, value_raw: str | None):
        self.type: str = value_type
        self.raw: str = f"{value_type}@{value_raw}"
        self.content: int | bool | str | float | None = value_raw

        if value_type == "nil" or value_raw is None:
            self.content = None
        elif value_type == "int":
            self.content = int(value_raw)
        elif value_type == "bool":
            if str(value_raw).lower() == "true":
                self.content = True
            else:
                self.content = False
        elif value_type == "string":
            pattern = re.compile(r"\\(\d{3})")

            def decode_esc(match):
                char_code = int(match.group(1), 10)
                return chr(char_code)

            try:
                self.content = pattern.sub(decode_esc, str(self.content)) or ""
            except ValueError:
                raise NameError(f"Invalid escape sequence: {self.content}")
        elif value_type == "float":
            self.content = float.fromhex(value_raw)
        elif value_type == "type":
            self.content = str(value_raw)
        else:
            raise TypeError(f"Invalid value type: {value_type}")

    def __repr__(self):
        return repr(self.content)

    def __str__(self):
        if self.type == "nil" or self.content is None:
            return ""
        if self.type == "float":
            return str(self.content.hex())
        if self.type == "bool":
            return str(self.content).lower()
        return str(self.content)

    def pyv(self):
        """Python hodnota premennej"""
        if self.type == "nil" or self.content is None:
            return ""
        return self.content


class UnresolvedVariable:
    """
    Trieda reprezentujúca premennú v argumente inštrukcie, ktorej je
    nutné počas interpretácie získať hodnotu (rieši execute_next())

    Atribúty:
        varid (str): IPPcode23 premenná (formát xF@id)

    Vyvolá:
        RuntimeError: pokiaľ je formát argumentu neplatný
    """

    def __init__(self, arg: str):
        self.frame, self.name = arg.split("@", maxsplit=1)
        if self.frame.upper() not in ("GF", "LF", "TF"):
            raise RuntimeError(f"Invalid variable name: {arg}")

    def __repr__(self):
        return f"{self.frame}@{self.name}"


class LabelArg:
    """Trieda reprezentujúca náveštie v skokovej inštrukcií"""

    def __init__(self, label: str):
        self.name: str = label

    def __repr__(self):
        return f"{self.name}"


class Frame:
    """Trieda reprezentujúca dátový rámec združujúci premenné"""

    def __init__(self):
        self._variables: dict[str, Value] = {}

    def __repr__(self):
        if self.size() == 0:
            return ""

        rstr = "\n".join(
            f"    {k} = {str(v.raw) if isinstance(v, Value) else repr(v)}"
            for k, v in self._variables.items()
        )
        return f"{rstr}\n"

    def size(self) -> int:
        """Získa počet premenných v rámci"""
        return len(self._variables)

    def has_variable(self, name: str) -> bool:
        """Dotaz na existenciu premennej v rámci"""
        return name in self._variables

    def get_variable(self, name: str) -> Value:
        """Získa hodnotu premennej s daným názvom (neexistuje -> ENOVAR)"""
        if self.has_variable(name):
            return self._variables[name]
        raise KeyError(f"Couldn't access non-existant variable {name}")

    def define_variable(self, name: str) -> Value:
        """Deklaruje novú premennú v rámci (redeklarácia -> ESEM)"""
        if not self.has_variable(name):
            self._variables[name] = None
        else:
            raise RuntimeError(f"Redefinition of variable {name}")

    def set_variable(self, name: str, value: Value):
        """Nastaví hodnotu premennej v rámci (neexistuje -> ENOVAR)"""
        if self.has_variable(name):
            self._variables[name]: Value = value
        else:
            raise KeyError(f"Couldn't set non-existant variable {name}")

    def delete_variable(self, name: str):
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
        self.opcode: str = opcode
        self.operands: list[Value | UnresolvedVariable | LabelArg] = operands

    def __repr__(self):
        operands = " ".join(
            [
                str(operand.raw) if isinstance(operand, Value) else repr(operand)
                for operand in self.operands
            ]
        )
        return f"{self.opcode} {operands}"

    def replace_operand(self, index: int, value: Value | UnresolvedVariable | LabelArg):
        """Nahradí operand inštrukcie na danom indexe"""
        self.operands[index] = value

    def next_unresolved(self) -> int:
        """Získa index ďalšieho nedefinovaného operandu (žiadny -> -1)"""
        for index, operand in enumerate(self.operands):
            if isinstance(operand, UnresolvedVariable):
                return index
        return -1
