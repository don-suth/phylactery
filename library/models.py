from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse

from taggit.managers import TaggableManager


class ItemTypes(models.Model):
    type_name = models.CharField(max_length=30)

    def __str__(self):
        return self.type_name


class Item(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, null=True)
    description = models.TextField(blank=True)
    condition = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    type = models.ForeignKey(ItemTypes, on_delete=models.PROTECT)
    tags = TaggableManager()

    def image_file_name(instance, filename):
        fname, dot, extension = filename.rpartition('.')
        return "library/item_images/{0}.{1}".format(instance.slug, extension)

    image = models.ImageField(upload_to=image_file_name, null=True)

    def get_absolute_url(self):
        return reverse('library:detail-slug', args=[self.slug])

    def __str__(self):
        return self.name
