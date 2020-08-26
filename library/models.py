from django.db import models
from django.core.exceptions import ValidationError


class ItemTypes(models.Model):
    type_name = models.CharField(max_length=30)


class Item(models.Model):
    item_name = models.CharField(max_length=200)
    item_condition = models.TextField()
    item_notes = models.TextField()
    item_type = models.ForeignKey(ItemTypes, on_delete=models.PROTECT)


class IntTag(models.Model):
    tag_name = models.CharField(max_length=30)
    tag_description = models.CharField(max_length=300)
    items = models.ManyToManyField(Item, through="IntTagValues")


class IntTagValues(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    tag = models.ForeignKey(IntTag, on_delete=models.PROTECT)
    value = models.IntegerField()


class StrTag(models.Model):
    tag_name = models.CharField(max_length=30)
    tag_description = models.CharField(max_length=300)
    items = models.ManyToManyField(Item, through="StrTagValues")


class StrTagValues(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    tag = models.ForeignKey(StrTag, on_delete=models.PROTECT)
    value = models.CharField(max_length=30)


class StaticTag(models.Model):
    tag_name = models.CharField(max_length=30)
    tag_description = models.CharField(max_length=300)
    items = models.ManyToManyField(Item)


