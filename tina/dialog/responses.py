import re


def yesorno(statement):
    statement = statement.lower()
    no_words = ["no", "nope", "not now", "negative", "sorry"]
    yes_words = ["yes", "yep", "absolutely", "go ahead", "sure", "definitely"]

    for word in no_words:
        if re.search(f"\\b{word}\\b", statement):
            return "no"

    for word in yes_words:
        if re.search(f"\\b{word}\\b", statement):
            return "yes"

    return None
