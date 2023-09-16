from django.conf import settings 

from django.core.validators import MinValueValidator 
from django.db import models
from users.models import User
from django.db.models import UniqueConstraint 
 
from colorfield.fields import ColorField 
 
 
 
class Ingredient(models.Model): 
    name = models.CharField( 
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH, 
        verbose_name="Ингредиент", 
        help_text="Введите название ингедиента", 
        db_index=True, 
    ) 
 
    measurement_unit = models.CharField( 
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH, 
        verbose_name="Единица измерения", 
        help_text="Введите название единицы измерения", 
        db_index=True, 
    ) 
 
    class Meta: 
        ordering = ["name"] 
        verbose_name = "Ингедиент" 
        verbose_name_plural = "Ингредиенты" 
        constraints = [ 
            UniqueConstraint( 
                fields=["name", "measurement_unit"], 
                name="ingredient_name_unit_unique" 
            ) 
        ] 
 
    def __str__(self): 
        return self.name 
 
 
class Tag(models.Model): 
    name = models.CharField(unique=True, 
                            max_length=settings.INGREDIENT_NAME_MAX_LENGTH, 
                            verbose_name="Тег", 
                            db_index=True,) 
 
    color_code = ColorField( 
        format="hex", 
        default="#FF0000", 
        verbose_name="Цвет", 
        help_text="Цветовой HEX-код", 
    ) 
 
    slug = models.SlugField( 
        unique=True, 
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH, 
        verbose_name="Слаг тега", 
        help_text="Введите слаг тега", 
        db_index=True, 
    ) 
 
    class Meta: 
        ordering = ["name"] 
        verbose_name = "Тег" 
        verbose_name_plural = "Теги" 
 
    def __str__(self): 
        return self.name 
 
 
class Recipe(models.Model): 
    author = models.ForeignKey( 
        User, 
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH, 
        on_delete=models.CASCADE, 
        related_name="recipes", 
        verbose_name="Автор рецепта", 
        db_index=True, 
    ) 
    name = models.CharField( 
        max_length=settings.INGREDIENT_NAME_MAX_LENGTH, 
        verbose_name="Название рецепта", 
        help_text="Введите название рецепта", 
        db_index=True, 
    ) 
    image = models.ImageField( 
        verbose_name="Картинка", 
        help_text="Загрузите ссылку на картинку к рецепту", 
        upload_to="recipes/images/", 
    ) 
    text = models.TextField( 
        max_length=1000, 
        verbose_name="Описание рецепта", 
        help_text="Введите описание рецепта", 
    ) 
    ingridients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient')
    )
    tags = models.ManyToManyField(Tag, 
                                  related_name="recipes", 
                                  verbose_name="Тэг") 
 
    cooking_time = models.PositiveIntegerField( 
        verbose_name="Время приготовления", 
        validators=[ 
            MinValueValidator( 
                1, message="Время приготовления должно быть не менее 1 минуты!" 
            ) 
        ], 
    ) 
    pub_date = models.DateTimeField( 
        "Время публикации", 
        auto_now_add=True, 
    ) 
 
    class Meta: 
        ordering = ("-pub_date",) 
        verbose_name = "Рецепт" 
        verbose_name_plural = "Рецепты" 
 
    def __str__(self): 
        return self.name 
 
 
class RecipeIngredient(models.Model): 
    recipe = models.ForeignKey( 
        Recipe, 
        on_delete=models.CASCADE, 
        related_name="ingredient_in_recipe", 
        verbose_name="Рецепт", 
    ) 
    ingredient = models.ForeignKey( 
        Ingredient, 
        on_delete=models.CASCADE, 
        related_name="ingredient_in_recipe", 
        verbose_name="Ингредиент", 
    ) 
    amount = models.PositiveIntegerField( 
        verbose_name="Количество ингредиента в рецепте", 
        validators=[ 
            MinValueValidator( 
                limit_value=0.1, message="Количество должно быть больше 0." 
            ), 
        ], 
    ) 
 
    class Meta: 
        verbose_name = "Связь ингредиента c рецептом" 
        verbose_name_plural = "Связи ингредиентов c рецептами" 
        default_related_name = "ingredients_recipe" 
        constraints = [ 
            models.UniqueConstraint( 
                name="unique_ingredient_recipe", 
                fields=["ingredient", "recipe"], 
            ), 
        ] 
 
    def __str__(self):
        return f'{self.ingredient} - {self.amount}'
 
 
 
class Favorite(models.Model): 
    user = models.ForeignKey( 
        User, 
        related_name="favorites", 
        on_delete=models.CASCADE, 
        verbose_name="Пользователь", 
    ) 
    recipe = models.ForeignKey( 
        Recipe, 
        related_name="favorite", 
        on_delete=models.CASCADE, 
        verbose_name="Избранный рецепт", 
    ) 
 
    class Meta: 
        ordering = ("user",) 
        constraints = [ 
            models.UniqueConstraint(fields=("user", "recipe"), 
                                    name="favorite_recipe") 
        ] 
        verbose_name = "Избранный" 
        verbose_name_plural = "Избранные" 
 
    def __str__(self): 
        return f"{self.recipe} - избранный рецепт для: {self.user}" 
 
 
class Shopping_list(models.Model): 
    user = models.ForeignKey( 
        User, on_delete=models.CASCADE, 
        verbose_name="Пользователь" 
    ) 
    recipe = models.ForeignKey( 
        Recipe, on_delete=models.CASCADE, 
        verbose_name="Рецепт в корзине" 
    ) 
 
    class Meta: 
        verbose_name = "Рецепт в корзине" 
        verbose_name_plural = "Рецепты в корзине" 
        constraints = ( 
            models.UniqueConstraint(fields=("user", "recipe"), 
                                    name="cart_is_unique"), 
        ) 
 
    def __str__(self): 
        return f"{self.recipe} планирует приготовить {self.user}" 
 