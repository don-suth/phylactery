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


def switch_to_proxy(user):
	"""
	Takes a User object and returns the UnigamesUser equivalent.
	"""
	if user.__class__ == User:
		user.__class__ = UnigamesUser
	return user


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
		super(Member, self).save(*args, **kwargs)

	def __str__(self):
		return str(self.preferred_name) + ' ' + str(self.last_name)

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
		return self.is_financial_member or self.has_rank('LIFEMEMBER')

	def get_most_recent_membership(self):
		# Returns the most recent membership object of this member, or None if they have none.
		return self.memberships.order_by('-date').first()

	@property
	def bought_membership_this_year(self):
		membership = self.get_most_recent_membership()
		if membership is not None:
			if membership.date.year == timezone.now().year:
				return True
		return False

	class Meta:
		ordering = ['first_name', 'last_name']


class Membership(models.Model):
	member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='memberships')
	phone_number = models.CharField(max_length=20, blank=True, validators=[RegexValidator(regex="^[0-9]+$")])
	date = models.DateField(default=timezone.now)
	guild_member = models.BooleanField()
	amount_paid = models.IntegerField()
	expired = models.BooleanField(default=False)
	authorising_gatekeeper = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, related_name='authorised', blank=True)
	auth_gatekeeper_name = models.CharField(max_length=400, blank=True)

	def __str__(self):
		return 'Membership for '+str(self.member)+' ('+str(self.date.__format__('%Y'))+')'

	def save(self, *args, **kwargs):
		if self.authorising_gatekeeper and not self.auth_gatekeeper_name:
			self.auth_gatekeeper_name = str(self.authorising_gatekeeper)
		elif not self.authorising_gatekeeper and not self.auth_gatekeeper_name:
			# Must've been set by the admin account for some reason
			self.auth_gatekeeper_name = 'Admin'
		super(Membership, self).save(*args, **kwargs)


class Rank(models.Model):
	RANK_CHOICES = [
		('EXCLUDED', 'Excluded'),
		('GATEKEEPER', 'Gatekeeper'),
		('WEBKEEPER', 'Webkeeper'),
		('COMMITTEE', 'Committee'),
		('LIFE-MEMBER', 'Life Member'),
		('PRESIDENT', 'President'),
		('VICE-PRESIDENT', 'Vice President'),
		('SECRETARY', 'Secretary'),
		('TREASURER', 'Treasurer'),
		('LIBRARIAN', 'Librarian'),
		('FRESHER-REP', 'Fresher Rep'),
		('OCM', 'OCM'),
		('IPP', 'IPP (Immediate Past President)')
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
	assignment_date = models.DateField(default=datetime.date.today)
	expired_date = models.DateField(blank=True, null=True)

	def __str__(self):
		return str(self.member) + ' (' + str(self.rank) + ')'


class MemberFlag(models.Model):
	name = models.CharField(max_length=20)
	description = models.CharField(max_length=200)
	active = models.BooleanField(default=True, help_text='Control whether this flag appears on membership forms')

	member = models.ManyToManyField(Member, related_name='flags')

	def __str__(self):
		return self.name
