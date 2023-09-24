from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import UniqueConstraint

from .validators import validate_username

username_validator = UnicodeUsernameValidator()


class User(AbstractUser):

    username = models.CharField(
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH_100,
        unique=True,
        verbose_name="Юзернейм",
        validators=[username_validator, validate_username],
        db_index=True,
    )
    first_name = models.CharField(
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH_100,
        blank=False,
        verbose_name="Имя",
        db_index=True,)
    last_name = models.CharField(
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH_100,
        blank=False,
        verbose_name="Фамилия",
        db_index=True,)
    email = models.EmailField(
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH_100,
        unique=True,
        verbose_name="Электронная почта",
        db_index=True,
    )
    password = models.CharField(
        verbose_name="Пароль",
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH_100,
    )
    is_subscribed = models.BooleanField(default=False)

    class Meta:
        ordering = ["username"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        constraints = [models.UniqueConstraint(
            fields=['username', 'email'], name='unigue_together')
        ]

    def __str__(self):
        return self.username


class Subscription(models.Model):

    user = models.ForeignKey(
        User,
        related_name="sub",
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        related_name="author",
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=["user", "author"],
                             name="user_author_unique")
        ]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"Пользователь {self.user} подписался на {self.author}"
