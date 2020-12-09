from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse

from taggit.managers import TaggableManager


class ItemTypes(models.Model):
    type_name = models.CharField(max_length=30)

    def __str__(self):
        return self.type_name


class Item(models.Model):
    item_name = models.CharField(max_length=200)
    item_slug = models.SlugField(max_length=50, null=True)
    item_description = models.TextField(blank=True)
    item_condition = models.TextField(blank=True)
    item_notes = models.TextField(blank=True)
    item_type = models.ForeignKey(ItemTypes, on_delete=models.PROTECT)
    tags = TaggableManager()

    def image_file_name(instance, filename):
        fname, dot, extension = filename.rpartition('.')
        return "library/item_images/{0}.{1}".format(instance.item_slug, extension)

    item_image = models.ImageField(upload_to=image_file_name, null=True)

    def get_absolute_url(self):
        return reverse('library:detail-slug', args=[self.item_slug])

    def __str__(self):
        return self.item_name
