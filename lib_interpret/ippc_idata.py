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
        self._items = []

    def __repr__(self):
        if self.is_empty():
            return "  > (empty)\n"
        return (
            "  >  " + "\n     ".join(str(item) for item in reversed(self._items)) + "\n"
        )

    def is_empty(self):
        """
        Dotaz na prázdnosť zásobníka.

        Vráti:
            bool: true, pokiaľ je zásobník prázdny, inak false
        """
        return len(self._items) == 0

    def push(self, item):
        """
        Pridá položku na vrchol zásobníka.

        Argumenty:
            item (any): položka na pridanie
        """
        self._items.append(item)

    def pop(self):
        """
        Odoberie a vráti položku z vrcholu zásobníka.

        Vráti:
            any: položka z vrcholu zásobníka

        Vyvolá:
            RuntimeError: pokiaľ je zásobník prázdny
        """
        if not self.is_empty():
            return self._items.pop()
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
            return self._items[-1]
        raise RuntimeError("Cannot access empty stack")

    def size(self):
        """
        Vráti počet položiek v zásobníku.

        Vráti:
            int: počet položiek v zásobníku
        """
        return len(self._items)


class Queue:
    """
    Fronta pre inštrukcie a vstup.

    Argumenty:
        _queue (list): zoznam, ktorý reprezentuje frontu
    """

    def __init__(self):
        self._items = []

    def __repr__(self):
        if self.is_empty():
            return "  > (empty)\n"
        return "  >  " + "\n     ".join(str(item) for item in self._items) + "\n"

    def is_empty(self):
        """
        Dotaz na prázdnosť fronty.

        Vráti:
            bool: true, pokiaľ je fronta prázdna, inak false
        """
        return len(self._items) == 0

    def enqueue(self, item):
        """
        Pridá položku na koniec fronty.

        Argumenty:
            item (any): položka na pridanie
        """
        self._items.append(item)

    def dequeue(self):
        """
        Odoberie a vráti položku zo začiatku fronty.

        Vráti:
            any: položka zo začiatku fronty

        Vyvolá:
            RuntimeError: pokiaľ je fronta prázdna
        """
        if not self.is_empty():
            return self._items.pop(0)
        raise RuntimeError("Cannot access empty queue")

    def size(self):
        """
        Vráti počet položiek v fronte.

        Vráti:
            int: počet položiek v fronte
        """
        return len(self._items)


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

    def __repr__(self):
        return f"{self.type}@{self.value}"


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
