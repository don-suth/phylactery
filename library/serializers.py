from rest_framework import serializers
from library.models import Item


class ItemSerialiser(serializers.ModelSerializer):
	class Meta:
		model = Item
		fields = ['id', 'name', 'description', 'url', 'type', 'is_borrowable', 'image', 'availability']
