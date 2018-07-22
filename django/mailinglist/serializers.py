from django.contrib.auth import get_user_model

from rest_framework import serializers

from mailinglist.models import (MailingList, Subscriber,)


class MailingListSerializer(serializers.HyperlinkedModelSerializer):
    '''
    MailingListSerializer for a MailingList model instances.

    Owner field of MailingList is overridden because related to a field User
        model doesn't have a serializer.
    '''
    owner = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )

    class Meta:
        model = MailingList
        fields = ('url', 'id', 'name', 'owner', 'subscriber_set')
        read_only_fields = ('subscriber_set',)
        extra_kwargs = {
            'url': {'view_name': 'mailinglist:api-mailing-list-detail'},
            'subscriber_set': {
                'view_name': 'mailinglist:api-subscriber-detail'
            },
        }


class SubscriberSerializer(serializers.HyperlinkedModelSerializer):
    '''
    SubscriberSerializer for a Subscriber model instances.

    Email field is exposed for modification so this serializer should be used
        when user creates a new subscriber for a mailinglist and provides an
        email.
    '''
    class Meta:
        model = Subscriber
        fields = ('url', 'id', 'email', 'confirmed', 'mailing_list')
        extra_kwargs = {
            'url': {'view_name': 'mailinglist:api-subscriber-detail'},
            'mailing_list': {
                'view_name': 'mailinglist:api-mailing-list-detail'
            },
        }


class ReadOnlyEmailSubscriberSerializer(
    serializers.HyperlinkedModelSerializer
):
    '''
    SubscriberSerializer for a Subscriber model instances.

    Email and mailing_list fields are read only so this serializer should be
        used to retrieve existing Subscriber instance.
    '''
    class Meta:
        model = Subscriber
        fields = ('url', 'id', 'email', 'confirmed', 'mailing_list')
        read_only_fields = ('email', 'mailing_list')
        extra_kwargs = {
            'url': {'view_name': 'mailinglist:api-subscriber-detail'},
            'mailing_list': {
                'view_name': 'mailinglist:api-mailing-list-detail'
            },
        }
