# celery tasks going here
from celery import shared_task

from mailinglist import emails


@shared_task
def send_confirmation_email_to_subscriber(subscriber_id):
    # import it here to prevent a cyclic import error
    from mailinglist.models import Subscriber 
    '''
    Task function queries Subscriber model for a given subscriber_id and
        creates a task to to send a confirmation email to a subscriber using
        send_confirmation_email helper function.

    Args:
        subscriber_id - uuid
    '''
    subscriber = Subscriber.objects.get(id=subscriber_id)
    emails.send_confirmation_email(subscriber)


@shared_task
def build_subscriber_messages_for_message(message_id):
    # import it here to prevent a cyclic import error
    from mailinglist.models import Message, SubscriberMessage
    '''
    Function asynchronously creates SubscriberMessage model instances related
        to a given Message.

    Args:
        subscriber_id - uuid
    '''
    message = Message.objects.get(id=message_id)
    SubscriberMessage.objects.create_from_message(message)


@shared_task
def send_subscriber_message(subscriber_message_id):
    # import it here to prevent a cyclic import error
    from mailinglist.models import SubscriberMessage
    subscriber_message = SubscriberMessage.objects.get(
        id=subscriber_message_id
    )
    emails.send_subscriber_message(subscriber_message)
