from enum import Enum

class Languages(str, Enum):
    """Enumeration to represent the available languages.

    Attributes:
        EN (str): English language.
        ES (str): Spanish language.
    """
    EN = "en"
    ES = "es"
