from django.db import models


# Create your models here.
class Member(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    preferred_name = models.CharField(max_length=200)
    pronouns = models.CharField(max_length=200)
    email_address = models.CharField(max_length=200)
    student_number = models.CharField(max_length=10)
	join_date = models.DateField(auto_now_add=True)
    notes = models.TextField()

    def __str__(self):
        return self.preferred_name + ' ' + self.last_name + ' (' + self.pronouns + ')'


class Membership(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    guild_member = models.BooleanField()


class Ranks(models.Model):
    rank_name = models.CharField(max_length=50)
    member = models.ManyToManyField(Member)
