from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
	username = None
	email = models.EmailField(max_length=64, unique=True)
	token = models.CharField(max_length=100)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	def __str__(self):
		return self.email

class Repository(models.Model):
	repository_id = models.AutoField(primary_key=True)
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	auth_token = models.CharField(max_length=128)
	url = models.URLField(unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return str(self.url)

class TrafficEvent(models.Model):
	repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="traffic")
	timestamp = models.DateTimeField()
	count = models.IntegerField()
	uniques = models.IntegerField()

	class Meta:
		unique_together = ('repository', 'timestamp',)

	def __str__(self):
		return "{}: Count={}, Unique={}".format(self.timestamp.strftime("%Y-%m-%d"), self.count, self.uniques)