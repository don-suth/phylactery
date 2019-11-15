from django.db import models

# Create your models here.
class Member(models.model):
	first_name = models.Charfield(max_length=200)
	last_name = models.Charfield(max_length=200)
	preferred_name = models.Charfield(max_length=200)
	pronouns = models.Charfield(max_length=200)
	email_address = model.Charfield(max_length=200)
	student_number
	notes TextField
	
class Membership(models.model)
	member FK
	date
	guild_member
	
class Ranks
	rank_name unique
	member M2M
	permissions
