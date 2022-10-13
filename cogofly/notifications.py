from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from .models import Activity, Trip, Comment, Notification, User
from django.db import transaction
from django.utils.translation import ngettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

@transaction.atomic()
def notify(user, obj, ntype, args = None):
    if args is None:
        args = {}
    notification, created = user.notifications.get_or_create(
        content_type = ContentType.objects.get_for_model(obj),
        object_id = obj.id,
        type = ntype
    )
    notification.text = Notification.Types.labels[ntype] % {'object': obj.__class__.__name__.lower(), **args}
    notification.updated = timezone.now()
    notification.read = False
    notification.save()

@receiver(post_save, sender=Activity)
def react(**kwargs):
    react = kwargs.get('instance')
    count = react.content_object.reactions.filter(activity=react.activity).count()
    notify(react.content_object.user, react.content_object, react.activity, {
        'name': react.user, 
        'value': count - 1,
        'count': count
    })
               
@receiver(post_save, sender=Comment)
def comment(**kwargs):
    comment = kwargs.get('instance')
    count = comment.post.comments.values('user').distinct().count()
    if comment.user != comment.post.user:
        notify(comment.post.user, comment.post, Notification.Types.COMMENT_OWN_POST, {
                'name': comment.user, 
                'value': count - 1,
                'count': count
            })
    other_users = [com.user for com in comment.post.comments.exclude(user=comment.post.user).exclude(user=comment.user)]
    for user in other_users:
        notify(user, comment.post, Notification.Types.COMMENT_SAME_POST, {
            'name': comment.user, 
            'value': count - 1,
            'count': count
        })

@receiver(post_save, sender=Trip)
def trip_created(created, **kwargs):
    trip = kwargs.get('instance')
    if created:
        for user in trip.user.contacts.all():
            notify(user, trip, Notification.Types.ADD_TRIP, {'name': trip.user})

@receiver(m2m_changed, sender=Trip.members.through)
def new_member(action, **kwargs):
    if action == 'pre_add':
        trip = kwargs.get('instance')
        pk_set = list(kwargs.get('pk_set'))
        if pk_set:
            added_user = User.objects.get(pk=pk_set[0])
            if added_user != trip.user:
                notify(added_user, trip, Notification.Types.TRIP_REQUEST_ACCEPTED)
            for user in (trip.members.all() | added_user.contacts.all()).distinct():
                notify(user, trip, Notification.Types.JOIN_SAME_TRIP if user in trip.members.all() else Notification.Types.JOIN_ANY_TRIP , {'name': added_user})

@receiver(m2m_changed, sender=User.contacts.through)
def new_contact(action, **kwargs):
    if action == 'pre_add':
        user = kwargs.get('instance')
        pk_set = list(kwargs.get('pk_set'))
        if pk_set:
            added_user = User.objects.get(pk=pk_set[0])
            notify(added_user, user, Notification.Types.NEW_FRIEND, {'name': user})
            notify(user, added_user, Notification.Types.NEW_FRIEND, {'name': added_user})