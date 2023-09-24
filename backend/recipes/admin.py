from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Shopping_list,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "in_favorite")
    list_filter = ['tags']
    search_fields = ("name", "author__username")
    inlines = [RecipeIngredientInline]

    @admin.display(description='В избранном')
    def in_favorite(self, obj):
        return obj.favorite.all().count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "color_code", "slug")


@admin.register(Favorite)
class FavoritesAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "ingredient", "amount")
    list_editable = ("amount",)


@admin.register(Shopping_list)
class Shopping_list(admin.ModelAdmin):
    list_display = ("user", "recipe")
