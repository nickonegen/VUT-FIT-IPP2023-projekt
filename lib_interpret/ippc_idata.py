"""
Pomocné triedy a konštanty pre interpret.py
@author: Onegen Something <xonege99@vutbr.cz>
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
    "EVALUE": 57,  # Chybná hodnota
    "ESTR": 58,  # Nesprávne zaobchádzanie s reťazcom
}

IEXCEPTIONC = {
    RuntimeError: "ESEM",
    AttributeError: "EPARAM",
    TypeError: "EOTYPE",
    KeyError: "ENOVAR",
    MemoryError: "ENOFRM",
    ValueError: "EVALUE",
    IndexError: "ENOVAL",
    NameError: "ESTR",
}


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
            any: položka na vrchole zásobníka, None ak je zásobník prázdny
        """
        if not self.is_empty():
            return self._items[-1]
        return None

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

    def top(self):
        """
        Vráti položku na začiatku fronty.

        Vráti:
            any: položka na začiatku fronty, None ak je fronta prázdna
        """
        if not self.is_empty():
            return self._items[0]
        return None

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

    Vyvolá:
        ValueError: pokiaľ je hodnota a typ nekompatibilné
    """

    def __init__(self, value_type, value_raw):
        self.type = value_type
        self.value = None
        match value_type:
            case "int":
                self.value = int(value_raw)
            case "bool":
                self.value = bool(value_raw)
            case "string":
                self.value = str(value_raw)
            case "float":
                self.value = float(value_raw)
            case "type":
                self.value = str(value_raw)
            case "nil":
                self.value = None

    def __repr__(self):
        return f"{self.type}@{self.value}"

    def __str__(self):
        match self.type:
            case "bool":
                return str(self.value).lower()
            case "nil":
                return ""
            case _:
                return str(self.value)
