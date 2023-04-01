from .models import Item
from .serializers import ItemSerialiser
from rest_framework import viewsets
from rest_framework.decorators import action
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import random


def get_random_pk(qs):
	pks = qs.values_list('pk', flat=True)
	chosen_pk = random.choice(pks)
	return chosen_pk


class ItemViewSet(viewsets.GenericViewSet):
	queryset = Item.objects.all()
	serializer_class = ItemSerialiser

	@action(detail=False)
	def all_items(self, request):
		qs = self.get_queryset()
		serialiser = self.get_serializer(qs, many=True)
		return JsonResponse(serialiser.data, safe=False)

	@action(detail=True)
	def random_item(self, request):
		qs = self.get_queryset()
		chosen_item = get_object_or_404(Item, pk=get_random_pk(qs))
		serialiser = self.get_serializer(chosen_item)
		return JsonResponse(serialiser.data, safe=False)

	@action(detail=True)
	def random_book(self, request):
		qs = self.get_queryset().filter(type='BK')
		chosen_item = get_object_or_404(Item, pk=get_random_pk(qs))
		serialiser = self.get_serializer(chosen_item)
		return JsonResponse(serialiser.data, safe=False)

	@action(detail=True)
	def random_boardgame(self, request):
		qs = self.get_queryset().filter(type='BG')
		chosen_item = get_object_or_404(Item, pk=get_random_pk(qs))
		serialiser = self.get_serializer(chosen_item)
		return JsonResponse(serialiser.data, safe=False)

	@action(detail=True)
	def random_cardgame(self, request):
		qs = self.get_queryset().filter(type='CG')
		chosen_item = get_object_or_404(Item, pk=get_random_pk(qs))
		serialiser = self.get_serializer(chosen_item)
		return JsonResponse(serialiser.data, safe=False)
