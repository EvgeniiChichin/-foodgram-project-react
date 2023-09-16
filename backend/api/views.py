from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CustomUserSerializer, FavoriteSerializer, FollowSerializer,
    IngredientSerializer, RecipeCreateUpdateSerializer, RecipeSerializer,
    TagSerializer
)
from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, Shopping_list, Tag
)
from users.models import Subscription, User


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    @action(['POST', 'DELETE'], detail=True)
    def subscribe(self, request, **kwargs):
        user = request.user
        author = get_object_or_404(User, id=kwargs.get('id'))
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'На себя подписаться нельзя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Subscription.objects.create(
                user=user, author=author
            )
            serializer = FollowSerializer(
                follow, context={'request': request}
            )
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        follow = Subscription.objects.filter(user=user, author=author)
        if follow.exists():
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Вы не подписаны на этого автора'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = Subscription.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return RecipeCreateUpdateSerializer

    def add_favorites(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if model.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance = model.objects.create(user=request.user, recipe=recipe)
        serializer = FavoriteSerializer(
            instance, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_favorites(self, model, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if get_object_or_404(model, user=request.user, recipe=recipe).delete():
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Этот рецепт еще не добавлен'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        ['POST', 'DELETE'], detail=True, permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, **kwargs):
        if request.method == 'POST':
            return self.add_favorites(Favorite, request, kwargs.get('pk'))
        return self.delete_favorites(Favorite, request, kwargs.get('pk'))

    @action(
        ['POST', 'DELETE'], detail=True, permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, **kwargs):
        if request.method == 'POST':
            return self.add_favorites(Shopping_list, request, kwargs.get('pk'))
        return self.delete_favorites(Shopping_list, request, kwargs.get('pk'))

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = (RecipeIngredient.objects.filter(
            recipe__shopping_recipe__user=request.user
        ).values(
            'ingredient'
        ).order_by(
            'ingredient__name'
        ).annotate(
            total_amount=Sum('amount')
        ).values_list(
            'ingredient__name', 'total_amount', 'ingredient__measurement_unit'
        ))
        shopping_cart = []
        for ingredient in ingredients:
            shopping_cart.append(
                f'{ingredient[0]} ({ingredient[2]}) - {ingredient[1]}\n'
            )
        response = HttpResponse(shopping_cart, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping.txt"'
        return response