import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class MailingList(models.Model):
    '''
    MailingList.Model

    Id field made muted and nonsequential due to being publicly exposed to
        users.
    '''
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=140)
    owner = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            'mailinglist:manage_mailinglist',
            kwargs={'pk': self.id}
        )

    def user_can_use_mailing_list(self, user):
        # checks whether request.user can use this mailing list
        return user == self.owner


class Subscriber(models.Model):
    '''
    Subscriber.Model

    Has one-to-many relation to MailingList model object.

    Id field made muted and nonsequential due to being publicly exposed to
        users.
    Subscriber with given email field can subscribe to a specific
        mailing_list only once.
    '''
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField()
    confirmed = models.BooleanField(default=False)
    mailing_list = models.ForeignKey(to=MailingList, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['email', 'mailing_list',]


class Message(models.Model):
    '''
    Message.Model

    Has one-to-many relation to MailingList model object.
    '''
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    mailing_list = models.ForeignKey(to=MailingList, on_delete=models.CASCADE)
    subject = models.CharField(max_length=140)
    body = models.TextField()
    started = models.DateTimeField(default=None, null=True)
    finished = models.DateTimeField(default=None, null=True)
