"""
Pomocné triedy pre interpret.py
@author: Onegen Something <xonege99@vutbr.cz>
"""


class Stack:
    """
    Zásobník pre rámce a hodnoty.

    Argumenty:
        _stack (list): zoznam, ktorý reprezentuje zásobník
    """

    def __init__(self):
        self._stack = []

    def is_empty(self):
        """
        Dotaz na prázdnosť zásobníka.

        Vráti:
            bool: true, pokiaľ je zásobník prázdny, inak false
        """
        return len(self._stack) == 0

    def push(self, item):
        """
        Pridá položku na vrchol zásobníka.

        Argumenty:
            item (any): položka na pridanie
        """
        self._stack.append(item)

    def pop(self):
        """
        Odoberie a vráti položku z vrcholu zásobníka.

        Vráti:
            any: položka z vrcholu zásobníka

        Vyvolá:
            RuntimeError: pokiaľ je zásobník prázdny
        """
        if not self.is_empty():
            return self._stack.pop()
        else:
            raise RuntimeError("Cannot access empty stack")

    def top(self):
        """
        Vráti položku na vrchole zásobníka.

        Vráti:
            any: položka na vrchole zásobníka

        Vyvolá:
            RuntimeError: pokiaľ je zásobník prázdny
        """
        if not self.is_empty():
            return self._stack[-1]
        else:
            raise RuntimeError("Cannot access empty stack")


class Value:
    """
    Trieda pre reprezentáciu hodnoty v IPPcode23.

    Argumenty:
        type (str): typ hodnoty
        value (any): hodnota
    """

    def __init__(self, value_type, value):
        self.type = value_type
        self.value = value

    def __str__(self):
        return f"{self.type}: {self.value}"


class UnresolvedVariable:
    """
    Trieda reprezentujúca premennú v argumente inštrukcie, ktorá bude
    počas interpretácie nahradená jej hodnotou.

    Argumenty:
        frame (str): identifikátor rámca (GF, LF, TF)
        name (str): názov premennej
    """

    def __init__(self, arg):
        self.frame, self.name = arg.split("@", maxsplit=1)
        if self.frame.upper() not in ("GF", "LF", "TF"):
            raise ValueError(f"Invalid variable name: {arg}")
