from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView,)

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from mailinglist.forms import (MailingListForm, MessageForm, SubscriberForm,)
from mailinglist.mixins import UserCanUseMailingList
from mailinglist.models import (MailingList, Subscriber, Message,)
from mailinglist.permissions import CanUseMailingList
from mailinglist.serializers import (
    MailingListSerializer, SubscriberSerializer,
    ReadOnlyEmailSubscriberSerializer,
)


# http://localhost:8000/mailinglist
class MailingListListView(LoginRequiredMixin, ListView):
    '''
    Shows the mailing lists a logined user owns.
    '''
    def get_queryset(self):
        return MailingList.objects.filter(owner=self.request.user)


# http://localhost:8000/mailinglist/new
class CreateMailingListView(LoginRequiredMixin, CreateView):
    '''
    View used to create MailingLists via MailingListForm.
    '''
    form_class = MailingListForm
    template_name = 'mailinglist/mailinglist_form.html'

    def get_initial(self):
        return {
            'owner': self.request.user.id,
        }


# http://localhost:8000/mailinglist/<uuid:pk>/delete
class DeleteMailingListView(LoginRequiredMixin, UserCanUseMailingList, 
                            DeleteView):
    '''
    Allows user to delete MailingList if user is logged in and authorized
        to manipulate with a given MailingList.
    Args:
        <uuid:pk> - unique id given to a view as a pk
    '''
    model = MailingList
    success_url = reverse_lazy('mailinglist:mailinglist_list')


# http://localhost:8000/mailinglist/<uuid:pk>/manage
class MailingListDetailView(LoginRequiredMixin, UserCanUseMailingList, 
                            DetailView):
    '''
    Renders details about MailingList to a logged in owner of a list.

    Args:
        <uuid:pk> - unique id given to a view as a pk
    '''
    model = MailingList


# http://localhost:8000/mailinglist/<uuid:mailinglist_pk>/subscribe
class SubscribeToMailingListView(CreateView):
    '''
    View allows user to subscribe email to a MailingList.

    Args:
        <uuid:mailinglist_pk> - unique id of a MailingList
    '''
    form_class = SubscriberForm
    template_name = 'mailinglist/subscriber_form.html'

    def get_initial(self):
        return {
            'mailing_list': self.kwargs['mailinglist_pk']
        }

    def get_success_url(self):
        return reverse('mailinglist:subscriber_thankyou', kwargs={
            'pk': self.object.mailing_list.id
        })

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mailing_list_pk = self.kwargs['mailinglist_pk']
        ctx['mailing_list'] = get_object_or_404(
            MailingList,
            pk=mailing_list_pk
        )
        return ctx


# http://localhost:8000/mailinglist/<uuid:pk>/thankyou
class ThankYouForSubscribingView(DetailView):
    '''
    Thank you page for a user subscribed email to a MailingList.

    Args:
        <uuid:pk> - unique id for a MailingList
    '''
    model = MailingList
    template = 'mailinglist/subscription_thankyou.html'


# http://localhost:8000/mailinglist/subscribe/confirmation/<uuid:pk>
class ConfirmSubscriptionView(DetailView):
    '''
    View confirms an email subscribed by a user to a mailing list.

    Args:
        <uuid:pk> - unique id for a Subscriber
    '''
    model = Subscriber
    template_name = 'mailinglist/confirm_subscription.html'

    def get_object(self, queryset=None):
        subscriber = super().get_object(queryset=queryset)
        subscriber.confirmed = True
        subscriber.save()
        return subscriber


# http://localhost:8000/mailinglist/unsubscribe/<uuid:pk>
class UnsubscribeView(DeleteView):
    '''
    View removes Subscriber with a given email from subscribers to MailingList
    
    Args:
        <uuid:pk> - unique id for a Subscriber
    '''
    model = Subscriber
    template_name = 'mailinglist/unsubscribe.html'

    def get_success_url(self):
        mailing_list = self.object.mailing_list
        return reverse('mailinglist:subscribe', kwargs={
            'mailinglist_pk': mailing_list.id
        })


# http://localhost:8000/mailinglist/<uuid:mailinglist_pk>/message/new
class CreateMessageView(LoginRequiredMixin, CreateView):
    '''
    View allows authorized user to create a Message for a MailingList and 
        shares it among Subscribers.

    Args:
        <uuid:mailinglist_pk> - unique id for a MailingList created Message is
            going to be related to
    '''
    SAVE_ACTION = 'save'
    PREVIEW_ACTION = 'preview'

    form_class = MessageForm
    template_name = 'mailinglist/message_form.html'

    def get_success_url(self):
        return reverse('mailinglist:manage_mailinglist', kwargs={
            'pk': self.object.mailing_list.id
        })

    def get_initial(self):
        # gets mailing_list value required by a muted form field
        mailing_list = self.get_mailing_list()
        return {
            'mailing_list': mailing_list.id,
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mailing_list = self.get_mailing_list()
        ctx.update({
            'mailing_list': mailing_list,
            'SAVE_ACTION': self.SAVE_ACTION,
            'PREVIEW_ACTION': self.PREVIEW_ACTION,
        })
        return ctx

    def form_valid(self, form):
        action = self.request.POST.get('action')
        if action == self.PREVIEW_ACTION:
            context = self.get_context_data(form=form, message=form.instance)
            return self.render_to_response(context=context)
        elif action == self.SAVE_ACTION:
            return super().form_valid(form)

    def get_mailing_list(self):
        # checks whether user can create a Message for a related MailingList
        mailing_list = get_object_or_404(
            MailingList,
            id=self.kwargs['mailinglist_pk']
        )
        if not mailing_list.user_can_use_mailing_list(self.request.user):
            raise PermissionDenied()
        return mailing_list


# http://localhost:8000/mailinglist/message/<uuid:pk>
class MessageDetailView(LoginRequiredMixin,
                        UserCanUseMailingList,
                        DetailView):
    '''
    View allows owner of MailingList to see all Messages he have created and
        sent to Subscribers of MailingList.

    Args:
        <uuid:pk> - int - id for a Message instance.
    '''
    model = Message


##############################################################################
##############################################################################
#
# API VIEWS LISTED BELOW
#
##############################################################################
##############################################################################

class MailingListCreateListView(generics.ListCreateAPIView):
    '''
    View allows to list and create MailingLists instance via API. 
    '''
    permission_classes = (IsAuthenticated, CanUseMailingList)
    serializer_class = MailingListSerializer

    def get_queryset(self):
        return self.request.user.mailinglist_set.all()

    def get_serializer(self, *args, **kwargs):
        # Method overrides the owner received as an input from the request
        # with the logged in user and ensures that a user can't manipulate a
        # MailingList already created by another user.
        if kwargs.get('data', None):
            data = kwargs.get('data', None)
            owner = {
                'owner': self.request.user.id,
            }
            data.update(owner)
        return super().get_serializer(*args, **kwargs)


class MailingListRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    '''
    View allows to perform CRUD operations on a MailingList instance via API.

    Args:
        <pk> - uuid for MailingList
    '''
    permission_classes = (IsAuthenticated, CanUseMailingList)
    serializer_class = MailingListSerializer
    queryset = MailingList.objects.all()


class SubscriberListCreateView(generics.ListCreateAPIView):
    '''
    View allows to list and create Subscriber instances via API.

    Args:
        <uuid:mailing_list_pk> - uuid for a related MailingList
    '''
    permission_classes = (IsAuthenticated, CanUseMailingList)
    serializer_class = SubscriberSerializer

    def get_queryset(self):
        # method checks whether MailingList model instance indentified in the
        # URL before returning queryset of all related Subscriber instances.
        mailing_list_pk = self.kwargs['mailing_list_pk']
        mailing_list = get_object_or_404(MailingList, id=mailing_list_pk)
        return mailing_list.subscriber_set.all()

    def get_serializer(self, *args, **kwargs):
        # Method provides mailing_list field required by a serializer
        if kwargs.get('data'):
            data = kwargs.get('data')
            mailing_list = {
                'mailing_list': reverse(
                    'mailinglist:api-mailing-list-detail',
                    kwargs={'pk': self.kwargs['mailing_list_pk']}
                )
            }
            data.update(mailing_list)
        return super().get_serializer(*args, **kwargs)


class SubscriberRetrieveUpdateDestroyView(
    generics.RetrieveUpdateDestroyAPIView
):
    '''
    View allows to perform CRUD operations on a Subscriber instance via API.

    Args:
        <uuid:pk> - uuid for MailingList
    '''
    permission_classes = (IsAuthenticated, CanUseMailingList)
    serializer_class = ReadOnlyEmailSubscriberSerializer
    queryset = Subscriber.objects.all()
