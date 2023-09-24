import re

from django.core.exceptions import ValidationError

FORBIDDEN_USERNAME = "me"
BAN = re.compile(r"[\w.@+-]+")


def validate_username(username):
    if username == FORBIDDEN_USERNAME:
        raise ValidationError(
            f"Использовать имя {FORBIDDEN_USERNAME}"
            f"в качестве username запрещено."
        )

    if not BAN.fullmatch(username):
        limited_characters = "".join(
            filter(lambda char: not char.isalnum()
                   and char not in "@.+-_", username)
        )
        raise ValidationError(
            f"В username допустимо использовать только буквы,"
            f"цифры и знаки @.+-_."
            f"Применение {limited_characters} запрещено."
        )
    return username
