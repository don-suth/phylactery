from django.db import models
from django.core.exceptions import ValidationError


class ItemTypes(models.Model):
    type_name = models.CharField(max_length=30)

    def __str__(self):
        return self.type_name


class Item(models.Model):
    item_name = models.CharField(max_length=200)
    item_condition = models.TextField()
    item_notes = models.TextField()
    item_type = models.ForeignKey(ItemTypes, on_delete=models.PROTECT)
    item_image = models.ImageField(upload_to='library/', null=True)

    def __str__(self):
        return self.item_name


class IntTag(models.Model):
    tag_name = models.CharField(max_length=30)
    tag_description = models.CharField(max_length=300)
    items = models.ManyToManyField(Item, through="IntTagValues")

    def __str__(self):
        return self.tag_name


class IntTagValues(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    tag = models.ForeignKey(IntTag, on_delete=models.PROTECT)
    value = models.IntegerField()

    def __str__(self):
        return str(self.tag.tag_name) + ": " + str(self.value)


class StrTag(models.Model):
    tag_name = models.CharField(max_length=30)
    tag_description = models.CharField(max_length=300)
    items = models.ManyToManyField(Item, through="StrTagValues")

    def __str__(self):
        return self.tag_name


class StrTagValues(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    tag = models.ForeignKey(StrTag, on_delete=models.PROTECT)
    value = models.CharField(max_length=30)

    def __str__(self):
        return str(self.tag.tag_name) + ": " + str(self.value)


class StaticTag(models.Model):
    tag_name = models.CharField(max_length=30)
    tag_description = models.CharField(max_length=300)
    items = models.ManyToManyField(Item)

    def __str__(self):
        return self.tag_name


