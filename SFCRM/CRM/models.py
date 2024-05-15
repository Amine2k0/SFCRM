from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class CustomUser(AbstractUser):
    age=models.IntegerField(default=0)   
    adress=models.CharField(max_length=250) 


class Client(CustomUser): 
    rep=models.CharField(max_length=3,default='No')

class Agent(CustomUser):
    Dispo=models.BooleanField(default=True) 
    def save(self, *args, **kwargs):
      if not self.pk: 
        self.set_password(self.password)
      super().save(*args, **kwargs)


class Ticket(models.Model):
    Subject=models.CharField(max_length=350)
    Date=models.DateTimeField(auto_now_add=True)
    Status=models.CharField(max_length=20)
    Urgent=models.BooleanField(default=False)
    Client=models.ForeignKey(Client, on_delete=models.CASCADE)
    Agent=models.ForeignKey(Agent, on_delete=models.CASCADE)
    