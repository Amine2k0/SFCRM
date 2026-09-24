from django.contrib.auth.models import AbstractUser
from django.db import models


class TicketStatus(models.TextChoices):
    """The states a ticket moves through.

    Defined once here so the model, the edit form and the list filter cannot
    drift apart. The values match the strings already stored in the database.
    """

    OPEN = "Open", "Open"
    PENDING = "Pending", "Pending"
    SOLVED = "Solved", "Solved"
    CLOSED = "Closed", "Closed"


class CustomUser(AbstractUser):
    age = models.IntegerField(default=0)
    adress = models.CharField(max_length=250)


class Client(CustomUser):
    rep = models.CharField(max_length=3, default="No")


class Agent(CustomUser):
    Dispo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.set_password(self.password)
        super().save(*args, **kwargs)


class Ticket(models.Model):
    Subject = models.CharField(max_length=350)
    Date = models.DateTimeField(auto_now_add=True)
    Status = models.CharField(
        max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN
    )
    Urgent = models.BooleanField(default=False)
    Client = models.ForeignKey(Client, on_delete=models.CASCADE)
    Agent = models.ForeignKey(Agent, on_delete=models.CASCADE)

    class Meta:
        # Newest first. Pagination needs a deterministic order, or rows drift
        # between pages; id breaks ties when two tickets share a timestamp.
        ordering = ["-Date", "-id"]

    def __str__(self):
        return f"#{self.pk} {self.Subject}"
