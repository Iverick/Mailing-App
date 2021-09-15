import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from mailinglist import emails, tasks


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


class SubscriberManager(models.Manager):
    '''
    Manager for a Subscribe model. Returns list of subscribers with confirmed
        status related to a given mailing_list.
    '''
    def confirmed_subscribers_for_mailing_list(self, mailing_list):
        qs = self.get_queryset()
        qs = qs.filter(confirmed=True)
        qs = qs.filter(mailing_list=mailing_list)
        return qs


class Subscriber(models.Model):
    '''
    Subscriber.Model

    Has one-to-many relation to MailingList model object.

    Id field made muted and nonsequential due to being publicly exposed to
        users.
    Subscriber with a given email field can subscribe to a specific
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
    objects = SubscriberManager()

    class Meta:
        unique_together = ['email', 'mailing_list',]

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # Calls send_confirmation_email method if object has been added to
        # a database and isn't confirmed yet.
        is_new = self._state.adding or force_insert
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        if is_new and not self.confirmed:
            self.send_confirmation_email()

    def send_confirmation_email(self):
        # Adds send_confirmation_email_to_subscriber asynchronous task to a
        # Celery's message broker.
        tasks.send_confirmation_email_to_subscriber.delay(self.id)


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

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # Adds build_subscriber_messages_for_message asynchronous task to a
        # queue for execution if object has been added to a database.
        is_new = self._state.adding or force_insert
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        if is_new:
            tasks.build_subscriber_messages_for_message.delay(self.id)


class SubscriberMessageManager(models.Manager):
    '''
    Manager for a SubscriberMessage model.
    '''
    def create_from_message(self, message):
        '''
        Method allows to create SubscriberMessage instance of Message, returns
            a list of SubscriberMessages created using the Manager.create()
            method.
        '''
        confirmed_subs = Subscriber.objects.\
            send_confirmation_email(message.mailing_list)
        return [
            self.create(message=message, subscriber=subscriber)
            for subscriber in confirmed_subs
        ]


class SubscriberMessage(models.Model):
    '''
    SubscriberMessage.Model

    This model tracks whether message to a Subscriber has been
        successfully sent.

    Needs to be provided with message and subscriber fields to create an
        object.
    '''
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    message = models.ForeignKey(to=Message, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(to=Subscriber, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    sent = models.DateTimeField(default=None, null=True)
    last_attempt = models.DateTimeField(default=None, null=True)

    objects = SubscriberMessageManager()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # Calls send method if object has been added to a database
        is_new = self._state.adding or force_insert
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        if is_new:
            self.send()

    def send(self):
        # Calls tasks function to queue a task to send the message.
        tasks.send_confirmation_email_to_subscriber.delay(self.id)
