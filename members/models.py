import datetime
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


# Create your models here.
class Member(models.Model):
	first_name = models.CharField(max_length=200)
	last_name = models.CharField(max_length=200)
	preferred_name = models.CharField(max_length=200, blank=True)
	pronouns = models.CharField(max_length=200, blank=True)
	student_number = models.CharField(max_length=10, blank=True)
	email_address = models.CharField(max_length=200, blank=True, unique=True)
	phone_number = models.CharField(max_length=20, blank=True)
	join_date = models.DateField(default=datetime.date(2019, 1, 1))
	notes = models.TextField(blank=True)
	user = models.OneToOneField(User, blank=True, null=True, on_delete=models.SET_NULL)

	def clean(self):
		if not self.email_address and not self.student_number:
			raise ValidationError({'email_address': 'One of email address and student number must be filled out.'})

	def save(self, *args, **kwargs):
		if not self.preferred_name:
			self.preferred_name = self.first_name
		if not self.email_address and self.student_number:
			self.email_address = self.student_number+"@student.uwa.edu.au"
		super(Member, self).save(*args, **kwargs)

	def __str__(self):
		return self.preferred_name + ' ' + self.last_name

	def is_fresher(self):
		return self.join_date.year == timezone.now().year

	def has_rank(self, rank_name):
		for rank in self.ranks:
			if str(rank) == rank_name:
				return True
		return False


class Membership(models.Model):
	member = models.ForeignKey(Member, on_delete=models.CASCADE)
	date = models.DateField(default=timezone.now)
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


class Interest(models.Model):
	INTEREST_CHOICES = [
		('MAIL', 'Mailing List'),
		('FRESHERCAMPAIGN', 'Fresher Campaign'),
		('WARGAMING', 'Wargaming'),
		('MAGIC', 'Magic')
	]

	rank_name = models.CharField(
		max_length=20,
		choices=INTEREST_CHOICES
	)
	member = models.ManyToManyField(Member, related_name='interests')

	def __str__(self):
		return self.rank_name
