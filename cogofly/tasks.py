from django.utils.translation import gettext as _

from background_task import background

from .models import User
from .utils import send_mail

@background(schedule=5, remove_existing_tasks=True)
def hello(user_id):
	user = User.objects.get(id=user_id)
	context = {
		'user': user,
		**user.get_notifications_numbers(),
	}
	send_mail(user.email, _('Your notifications.'), 'email-notification.html', context)