from rest_framework.permissions import BasePermission

from mailinglist.models import (MailingList, Subscriber,)


class CanUseMailingList(BasePermission):
    '''
    Permission class for serializer.
    Checks whether user can perform operations with a MailingList or
        Subscriber models using MailingList's user_can_use_mailing_list()
        method.
    '''
    message = 'User does not have access to this resource.'

    def has_object_permission(self, request, view, obj):
        # Checks whether user is the owner of related MailingList.
        user = request.user
        if isinstance(obj, Subscriber):
            return obj.mailing_list.user_can_use_mailing_list(user)
        elif isinstance(obj, MailingList):
            return obj.user_can_use_mailing_list(user)
        return False
