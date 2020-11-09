from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse


class ItemTypes(models.Model):
    type_name = models.CharField(max_length=30)

    def __str__(self):
        return self.type_name


class Item(models.Model):
    item_name = models.CharField(max_length=200)
    item_slug = models.SlugField(max_length=50, null=True)
    item_condition = models.TextField(blank=True)
    item_notes = models.TextField(blank=True)
    item_type = models.ForeignKey(ItemTypes, on_delete=models.PROTECT)

    def image_file_name(instance, filename):
        fname, dot, extension = filename.rpartition('.')
        return "library/item_images/{0}.{1}".format(instance.item_slug, extension)

    item_image = models.ImageField(upload_to=image_file_name, null=True)

    def get_tags(self):
        tag_list = list()
        tag_list += list(self.inttags.all())
        tag_list += list(self.strtags.all())
        tag_list += list(self.statictags.all())
        tag_list.sort(key=lambda i: i.id)
        return tag_list

    def get_absolute_url(self):
        return reverse('library:detail-slug', args=[self.item_slug])

    def __str__(self):
        return self.item_name


class IntTag(models.Model):
    tag_name = models.CharField(max_length=30)
    tag_description = models.CharField(max_length=300)
    items = models.ManyToManyField(Item, through="IntTagValues")

    def __str__(self):
        return self.tag_name


class IntTagValues(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="inttags")
    tag = models.ForeignKey(IntTag, on_delete=models.PROTECT)
    value = models.IntegerField()

    def __str__(self):
        return str(self.tag.tag_name) + ": " + str(self.value)


class StrTag(models.Model):
    tag_name = models.CharField(max_length=30)
    tag_description = models.CharField(max_length=300)
    items = models.ManyToManyField(Item, through="StrTagThrough")

    def __str__(self):
        return self.tag_name


class StrTagValue(models.Model):
    tag = models.ForeignKey(StrTag, on_delete=models.PROTECT)
    value = models.CharField(max_length=30)

    def __str__(self):
        return self.value


class StrTagThrough(models.Model):
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="strtags")
    tag = models.ForeignKey(StrTag, on_delete=models.PROTECT)
    value = models.ForeignKey(StrTagValue, on_delete=models.PROTECT)

    def __str__(self):
        return str(self.tag.tag_name) + ": " + str(self.value)

    def clean(self, *args, **kwargs):
        if self.tag != self.value.tag:
            raise ValidationError("self.tag and self.value.tag must be identical")
        super(StrTagThrough, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(StrTagThrough, self).save(*args, **kwargs)

class StaticTag(models.Model):
    tag_name = models.CharField(max_length=30)
    tag_description = models.CharField(max_length=300)
    items = models.ManyToManyField(Item, related_name="statictags")

    def __str__(self):
        return self.tag_name


