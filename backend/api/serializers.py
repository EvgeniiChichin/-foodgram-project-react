from djoser.serializers import UserSerializer
from rest_framework.serializers import (
    IntegerField, ListField, ModelSerializer,
    PrimaryKeyRelatedField, ReadOnlyField, SerializerMethodField,
    ValidationError
)
from django.core.exceptions import ValidationError 
from django.contrib.auth.password_validation import validate_password 
 
from rest_framework import serializers 

from api.fields import Base64ImageField, ColorNameConverter 
 
from recipes.models import (Ingredient, Recipe, RecipeIngredient, Tag) 
from users.models import User, Subscription 
 

from djoser.serializers import UserCreateSerializer, UserSerializer

class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )
 


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField()
    new_password = serializers.CharField(write_only=True, required=False) 

    class Meta: 
        model = User 
        fields = [ 
            "id", 
            "email", 
            "username", 
            "first_name", 
            "last_name", 
            "is_subscribed", 
            "new_password", 
        ] 
 
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False
 
    def update(self, instance, validated_data): 
        """Обновляет данные пользователя, включая пароль.""" 
        new_password = validated_data.pop("new_password", None) 
        if new_password: 
            try: 
                validate_password(new_password, instance) 
 
            except ValidationError as e: 
                raise serializers.ValidationError(e.messages) 
 
            instance.set_password(new_password) 
 
            return super().update(instance, validated_data) 
 
 
class TagSerializer(ModelSerializer): 
    """Сериализатор для тегов.""" 
 
    color_code = ColorNameConverter() 
 
    class Meta: 
        model = Tag 
        fields = ("id", "name", "color_code", "slug") 
 
 
class IngredientSerializer(ModelSerializer): 
    """Сериализатор просмотра модели Ингредиенты.""" 
 
    class Meta: 
        model = Ingredient 
        fields = ["id", "name", "measurement_unit"] 
 
 
class RecipeIngredientSerializer(ModelSerializer): 
    """Сериализатор модели, связывающей ингредиенты и рецепт.""" 
 
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')
 
    class Meta: 
        model = RecipeIngredient 
        fields = ('id', 'name', 'amount', 'measurement_unit')
 
 
class RecipeIngredientCreateSerializer(ModelSerializer):
    id = IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')
 
 
class RecipeSerializer(ModelSerializer): 
    """ "Сериализатор для просмотра рецепта.""" 
 
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer( 
        source="ingredient_in_recipe", many=True, read_only=True) 
    is_favorited = serializers.SerializerMethodField() 
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True) 
 
    class Meta: 
        model = Recipe 
        fields = ( 
            "id", 
            "tags", 
            "author", 
            "ingredients", 
            "is_favorited", 
            "is_in_shopping_cart", 
            "name", 
            "image", 
            "text", 
            "cooking_time", 
        ) 
 
    def get_is_favorited(self, obj): 
        user = self.context["request"].user 
 
        return ( 
            user.is_authenticated 
            and obj.in_favorites.filter(user=user).exists() 
        ) 
 
    def get_is_in_shopping_cart(self, obj): 
        user = self.context["request"].user 
        return ( 
            user.is_authenticated 
            and obj.in_carts.filter(user=user).exists() 
        ) 
 
 
class RecipeCreateUpdateSerializer(ModelSerializer): 
    """ " Сериализатор для создания и обновления рецепта.""" 
 
    author = CustomUserSerializer(read_only=True)
    ingredients = ListField(
        child=RecipeIngredientCreateSerializer(), write_only=True
    )
    tags = ListField(
        child=PrimaryKeyRelatedField(queryset=Tag.objects.all()),
        write_only=True
    )
    image = Base64ImageField() 
 
    class Meta: 
        model = Recipe 
        fields = ( 
            "id",
            "tags", 
            "author", 
            "ingredients", 
            "name", 
            "image", 
            "text", 
            "cooking_time", 
        ) 
 
    def validate_tags(self, tags): 
        if not tags: 
            raise serializers.ValidationError("Необходимо выбрать теги!") 
        if len(tags) != len(set(tags)): 
            raise serializers.ValidationError("Теги должны быть уникальными!") 
        return tags 
 
    def validate_id(self, value): 
        if not Ingredient.objects.filter(id=value).exists(): 
            raise serializers.ValidationError( 
                'Ингредиент с данным id не существует') 
        return value 
 
    def validate_amount(self, value): 
        if value < 1: 
            raise serializers.ValidationError( 
                'Количество должно быть больше 0') 
        return value 

    def add_tags_ingredients(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])
    
    def create(self, validated_data): 
        ingredients = validated_data.pop("ingredients") 
        tags = validated_data.pop("tags") 
        recipe = Recipe.objects.create(**validated_data) 
        recipe.tags.set(tags) 
        ingredients_list = [ 
            RecipeIngredient( 
                recipe=recipe, 
                ingredient_id=ingredient["id"], 
                amount=ingredient["amount"], 
            ) 
            for ingredient in ingredients 
        ] 
        RecipeIngredient.objects.bulk_create(ingredients_list) 
        return recipe 
 
    def update(self, instance, validated_data): 
        instance.tags.clear() 
        instance.ingredients.clear() 
        tags = validated_data.pop("tags") 
        ingredients = validated_data.pop("ingredients") 
        super().update(instance, validated_data) 
        instance.tags.set(tags) 
        ingredients_list = [ 
            RecipeIngredient( 
                recipe=instance, 
                ingredient_id=ingredient["id"], 
                amount=ingredient["amount"], 
            ) 
            for ingredient in ingredients 
        ] 
        RecipeIngredient.objects.bulk_create(ingredients_list) 
        return instance 

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data
 
class RecipeFollowSerializer(ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')

 
class FollowSerializer(UserSerializer):
    id = ReadOnlyField(source='author.id')
    email = ReadOnlyField(source='author.email')
    username = ReadOnlyField(source='author.username')
    first_name = ReadOnlyField(source='author.first_name')
    last_name = ReadOnlyField(source='author.last_name')
    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipes_count = ReadOnlyField(source='author.recipes.count')

    class Meta:
        model = Subscription
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[:int(limit)]
        return RecipeFollowSerializer(queryset, many=True).data


class FavoriteSerializer(ModelSerializer):
    name = ReadOnlyField(source='recipe.name')
    image = Base64ImageField(source='recipe.image')
    cooking_time = ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')