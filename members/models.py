import datetime
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.validators import RegexValidator


# Create your models here.
class UnigamesUser(User):
	# Extends the base user class to add more functionality,
	class Meta:
		proxy = True

	@property
	def has_member(self):
		try:
			return self.member
		except Member.DoesNotExist:
			return None

	@property
	def is_gatekeeper(self):
		if self.is_superuser:
			return True
		member = self.has_member
		if member:
			return member.has_rank("GATEKEEPER")
		return False

	@property
	def is_committee(self):
		if self.is_superuser:
			return True
		member = self.has_member
		if member:
			return member.has_rank("COMMITTEE")
		return False


class Member(models.Model):
	first_name = models.CharField(max_length=200)
	last_name = models.CharField(max_length=200)
	preferred_name = models.CharField(max_length=200, blank=True)
	pronouns = models.CharField(max_length=200, blank=True)
	student_number = models.CharField(max_length=10, blank=True, validators=[RegexValidator(regex="^[0-9]+$")])
	email_address = models.EmailField(unique=True)
	join_date = models.DateField(default=datetime.date(2019, 1, 1))
	notes = models.TextField(blank=True)
	user = models.OneToOneField(UnigamesUser, blank=True, null=True, on_delete=models.SET_NULL, related_name='member')
	receive_emails = models.BooleanField(default=True)

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
		for rank in self.ranks.all():
			if str(rank) == rank_name:
				return True
		return False

	@property
	def is_gatekeeper(self):
		return self.has_rank('GATEKEEPER')

	@property
	def is_committee(self):
		return self.has_rank('COMMITTEE')

	@property
	def is_financial_member(self):
		return self.memberships.filter(expired=False).exists()

	@property
	def is_member(self):
		return self.is_financial_member() or self.has_rank('LIFEMEMBER')


class Membership(models.Model):
	member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='memberships')
	phone_number = models.CharField(max_length=20, blank=True, validators=[RegexValidator(regex="^[0-9]+$")])
	date = models.DateField(default=timezone.now)
	guild_member = models.BooleanField()
	amount_paid = models.IntegerField()
	expired = models.BooleanField(default=False)
	authorising_gatekeeper = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, related_name='authorised')


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
	member = models.ManyToManyField(Member, related_name='ranks', through="RankAssignments")

	def __str__(self):
		return self.rank_name


class RankAssignments(models.Model):
	member = models.ForeignKey(Member, on_delete=models.CASCADE)
	rank = models.ForeignKey(Rank, on_delete=models.CASCADE)
	assignment_date = models.DateField(auto_now_add=True)
	rank_expired = models.BooleanField(default=False)


class MemberFlag(models.Model):
	name = models.CharField(max_length=20)
	description = models.CharField(max_length=200)

	member = models.ManyToManyField(Member, related_name='flags')

	def __str__(self):
		return self.name
