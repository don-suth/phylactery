import datetime
from django.db import models
from django.utils import timezone

# Create your models here.
class Member(models.Model):
	first_name = models.CharField(max_length=200)
	last_name = models.CharField(max_length=200)
	preferred_name = models.CharField(max_length=200, blank=True)
	pronouns = models.CharField(max_length=200)
	email_address = models.CharField(max_length=200)
	student_number = models.CharField(max_length=10)
	join_date = models.DateField(default=timezone.now)
	notes = models.TextField(blank=True)

	def save(self, *args, **kwargs):
		if self.preferred_name == "":
			self.preferred_name = self.first_name
		super(Member, self).save(*args, **kwargs)


	def __str__(self):
		return self.preferred_name + ' ' + self.last_name

	def is_fresher(self):
		return self.join_date.year == timezone.now().year

class Membership(models.Model):
	member = models.ForeignKey(Member, on_delete=models.CASCADE)
	date = models.DateTimeField()
	guild_member = models.BooleanField()
	
class Rank(models.Model):
	RANK_CHOICES = [
		('SUSPENDED', 'Suspended'),
		('EXPELLED', 'Expelled'),
		('GATEKEEPER', 'Gatekeeper'),
		('WEBKEEPER', 'Webkeeper'),
		('COMMITTEE', 'Committee'),
		('LIFEMEMBER', 'Life Member')
	]
	rank_name = models.CharField(
		max_length=20,
		choices=RANK_CHOICES
	)
	member = models.ManyToManyField(Member, related_name='ranks')

	def __str__(self):
		return self.rank_name
