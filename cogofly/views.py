import datetime
import folium
import json
import unidecode

from functools import reduce
from operator import or_
from django.views.generic import TemplateView
from django.conf import settings
from django.contrib.auth.decorators import login_required

from django.contrib.auth.views import (
    LoginView,
    PasswordResetConfirmView,
    urlsafe_base64_decode,
    ValidationError,
)
from django.contrib.auth import login, logout, update_session_auth_hash

from django.core.paginator import Paginator

from django.views.generic import View, TemplateView

from django.shortcuts import render, redirect, reverse

from django.utils.translation import gettext as _

from django import db
from django.db.models import Count, Exists, OuterRef, Prefetch, Count, Max, F, Q

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.html import format_html
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from dal import autocomplete
from social_django.models import UserSocialAuth
from background_task.models import Task
from seo.models import PageNbVisites

from . import forms
from .models import *
from .tokens import account_activation_token
from .tasks import hello
from .utils import send_mail


def generate_map(points):
    m = folium.Map(width="100%", height="100%")
    min_lat, max_lat = 90.0, -90.0
    min_lon, max_lon = 180.0, -180.0
    for lat, lon, *rest in points:
        folium.Marker([lat, lon], *rest).add_to(m)
        min_lat, max_lat = min(lat, min_lat), max(lat, max_lat)
        min_lon, max_lon = min(lon, min_lon), max(lon, max_lon)
    bounds = [[float(min_lat), float(min_lon)], [float(max_lat), float(max_lon)]]
    m.fit_bounds(bounds, max_zoom=12)
    return m._repr_html_()


def near(place, d):
    return Q(
        profile__place__latitude__gt=place.latitude - d,
        profile__place__latitude__lt=place.latitude + d,
        profile__place__longitude__gt=place.longitude - d,
        profile__place__longitude__lt=place.longitude + d,
    )


def signup(request):
    if request.user.is_authenticated:
        return redirect("login")
    if request.method == "POST":
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.on_line = True
            user.save()

            context = {
                "user": user,
                "domain": settings.ALLOWED_HOSTS[0],
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": account_activation_token.make_token(user),
            }
            send_mail(
                form.cleaned_data.get("email"),
                _("Activate your CoGoFly account."),
                "confirmation_email.html",
                context,
                attachements="utils/CoGoFly User Charter Guide.pdf",
            )
            messages.add_message(
                request,
                messages.INFO,
                _("Please confirm your email address to complete the registration"),
            )
            return render(request, "auth-confirm.html")
    else:
        form = forms.SignUpForm()
    return render(request, "signup.html", {"form": form})


@login_required
def signup_next(request):
    if request.method == "POST":
        nameform = forms.NameForm(request.POST, instance=request.user)
        profileform = forms.ProfileForm(request.POST, request.FILES)
        if nameform.is_valid() and profileform.is_valid():
            nameform.save()
            profile = profileform.save(commit=False)
            profile.user = request.user
            profile.user.on_line = True
            profile.save()
            return redirect("home")
        # print(nameform.errors, profileform.errors)
    else:
        nameform = forms.NameForm(instance=request.user)
        profileform = forms.ProfileForm()
    return render(
        request, "signup-next.html", {"nameform": nameform, "profileform": profileform}
    )


class ProtectedMixin:
    def dispatch(self, request, *args, **kwargs):
        user_has_profile = hasattr(request.user, "profile")
        if not (user_has_profile and request.user.is_active):
            return redirect(reverse("signup-next"))
        return super().dispatch(request, *args, **kwargs)


class ContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context.update(self.request.user.get_notifications_numbers())
        context["shareform"] = forms.ShareForm()
        context["emailshareform"] = forms.EmailShareForm()
        return context


def landing(request):
    try:
        # Le compteur lié à la page est récupéré et incrémenté
        p = PageNbVisites.objects.get(url=request.path)
        p.nb_visites = F("nb_visites") + 1
        p.save()
    except PageNbVisites.DoesNotExist:
        # Un nouveau compteur à 1 par défaut est créé
        PageNbVisites(url=request.path).save()
    form = forms.SearchForm()
    # print(Search.objects.exclude(destination=None).prefetch_related('destination').order_by('created')[:5].values('created'))
    return render(
        request,
        "landing.html",
        {
            "form": form,
            "trips": Trip.objects.exclude(destination=None).prefetch_related(
                "destination"
            ),
            "last_searches_with_cities": Search.objects.exclude(
                destination=None
            ).prefetch_related("destination")[:21],
        },
    )


class AboutUsView(ContextMixin, TemplateView):
    template_name = "footer-about-us.html"


class TeamView(ContextMixin, TemplateView):
    template_name = "footer-the-team.html"


class ContactUsView(ContextMixin, TemplateView):
    template_name = "footer-contact-us.html"


class TestimonyView(ContextMixin, TemplateView):
    template_name = "footer-testimonies.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["testimonies"] = Testimony.objects.filter(accepted=True)
        return context


class BlogView(ContextMixin, TemplateView):
    template_name = "footer-blog.html"


class TermsConditionsView(ContextMixin, TemplateView):
    template_name = "footer-terms-and-conditions.html"


class PrivacyPolicyView(ContextMixin, TemplateView):
    template_name = "footer-privacy-policy.html"


class Covid(ContextMixin, TemplateView):
    template_name = "covid-19.html"


class DataDeletionInstructions(ContextMixin, TemplateView):
    template_name = "data-deletion-instructions.html"


def activate(request, uidb64, token):
    try:
        # Le compteur lié à la page est récupéré et incrémenté
        p = PageNbVisites.objects.get(url=request.path)
        p.nb_visites = F("nb_visites") + 1
        p.save()
    except PageNbVisites.DoesNotExist:
        # Un nouveau compteur à 1 par défaut est créé
        PageNbVisites(url=request.path).save()

    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User._base_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        if hasattr(user, "profile") and user.profile.email:
            user.email = user.profile.email
            user.profile.email = None
            user.profile.save()
        user.save()
        login(
            request,
            user,
            backend="django.contrib.auth.backends.AllowAllUsersModelBackend",
        )
        message = _("Your email is now verified.")
        messages.add_message(request, messages.SUCCESS, message)
        return redirect("home")
    else:
        messages.add_message(request, messages.INFO, _("Activation link is invalid!"))
        return render(request, "signup.html", {"form": forms.SignUpForm()})


from django.contrib.auth.forms import AuthenticationForm


class InactiveUsersPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = forms.SetPasswordShowForm

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User._base_manager.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user


class AuthenticationFormWithInactiveUsersOkay(AuthenticationForm):
    def confirm_login_allowed(self, user):
        pass


class CustomLoginView(LoginView):
    template_name = "login.html"
    form_class = AuthenticationFormWithInactiveUsersOkay

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        user = form.get_user()
        user.is_active = True
        user.on_line = True

        user.save()
        login(self.request, user)
        return redirect("home")


@login_required
def account(request):
    try:
        # Le compteur lié à la page est récupéré et incrémenté
        p = PageNbVisites.objects.get(url=request.path)
        p.nb_visites = F("nb_visites") + 1
        p.save()
    except PageNbVisites.DoesNotExist:
        # Un nouveau compteur à 1 par défaut est créé
        PageNbVisites(url=request.path).save()

    user = request.user
    PasswordForm = (
        forms.PasswordChangeShowForm
        if user.has_usable_password()
        else forms.SetPasswordShowForm
    )
    form = PasswordForm(request.user)
    delete_form = forms.DeleteAccountForm()
    deactivate_form = forms.DeactivateAccountForm()
    privacy_form = forms.PrivacyForm(instance=user.privacy)
    email_form = forms.ChangeEmailForm()
    frequency_form = forms.FrequencyForm(instance=user)

    if request.method == "POST":
        if "password" in request.POST:
            form = PasswordForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, _("Your password was successfully updated"))
        if "delete" in request.POST:
            delete_form = forms.DeleteAccountForm(request.POST)
            if delete_form.is_valid():
                request.user.is_active = False
                request.user.email = None
                request.user.first_name = ""
                request.user.last_name = ""
                request.user.save()
                UserSocialAuth.objects.filter(user=request.user).delete()
                messages.success(
                    request, _("Your account has been successfully deleted")
                )
                logout(request)
                return redirect("landing")
        if "deactivate" in request.POST:
            deactivate_form = forms.DeactivateAccountForm(request.POST)
            if deactivate_form.is_valid():
                request.user.is_active = False
                request.user.save()
                messages.success(
                    request, _("Your account has been successfully deactivated")
                )
                logout(request)
                return redirect("login")
        if "privacy" in request.POST:
            privacy_form = forms.PrivacyForm(
                request.POST, instance=request.user.privacy
            )
            if privacy_form.is_valid():
                privacy_form.save()
        if "changeemail" in request.POST:
            email_form = forms.ChangeEmailForm(
                request.POST, instance=request.user.profile
            )
            if email_form.is_valid():
                email_form.save()
                context = {
                    "user": user,
                    "domain": f"https://{request.get_host()}",
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": account_activation_token.make_token(user),
                }

                email = email_form.cleaned_data.get("email")
                send_mail(
                    email,
                    _("Confirm your new email adress."),
                    "confirmation_email.html",
                    context,
                )
                messages.add_message(
                    request,
                    messages.INFO,
                    _("We have sent you an email to confirm your new email address."),
                )
        if "cancelemail" in request.POST:
            request.user.profile.email = None
            request.user.profile.save()
            messages.add_message(
                request, messages.SUCCESS, _("New email successfully canceled")
            )
        if "frequency" in request.POST:
            frequency_form = forms.FrequencyForm(request.POST, instance=user)
            if frequency_form.is_valid():
                user = frequency_form.save()
                freq = user.notification_frequency
                if freq == User.Frequencies.NEVER:
                    hello(user.id, repeat=Task.NEVER)
                elif freq == User.Frequencies.DAILY:
                    hello(user.id, repeat=Task.DAILY)
                elif freq == User.Frequencies.WEEKLY:
                    hello(user.id, repeat=Task.WEEKLY)
                elif freq == User.Frequencies.MONTHLY:
                    hello(user.id, repeat=Task.EVERY_4_WEEKS)
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Notification frequency successfully changed"),
            )

    try:
        facebook_login = user.social_auth.get(provider="facebook")
    except UserSocialAuth.DoesNotExist:
        facebook_login = None

    try:
        linkedin_login = user.social_auth.get(provider="linkedin-oauth2")
    except UserSocialAuth.DoesNotExist:
        linkedin_login = None

    try:
        google_login = user.social_auth.get(provider="google-oauth2")
    except UserSocialAuth.DoesNotExist:
        google_login = None

    can_disconnect = user.social_auth.count() > 1 or user.has_usable_password()

    return render(
        request,
        "account.html",
        {
            "form": form,
            "privacy_form": privacy_form,
            "delete_form": delete_form,
            "deactivate_form": deactivate_form,
            "facebook_login": facebook_login,
            "linkedin_login": linkedin_login,
            "google_login": google_login,
            "can_disconnect": can_disconnect,
            "email_form": email_form,
            "frequency_form": frequency_form,
        },
    )


class ProfileView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "profile.html"

    def get(self, request, pk):
        try:
            # Le compteur lié à la page est récupéré et incrémenté
            p = PageNbVisites.objects.get(url=request.path)
            p.nb_visites = F("nb_visites") + 1
            p.save()
        except PageNbVisites.DoesNotExist:
            # Un nouveau compteur à 1 par défaut est créé
            PageNbVisites(url=request.path).save()
        user = (
            User.objects.select_related("profile")
            .prefetch_related(
                "profile__album",
                Prefetch(
                    "trips", queryset=Trip.objects.all().annotate_for(request.user)
                ),
                Prefetch(
                    "contacts", queryset=User.objects.all().annotate_for(request.user)
                ),
            )
            .annotate_for(request.user)
            .get(id=pk)
        )
        request.user.views.add(user)
        context = self.get_context_data()
        if user in request.user.contacts.all():
            action = "removecontact"
        elif user.requests.filter(user=request.user).exists():
            action = "cancelrequest"
        else:
            try:
                incoming = request.user.requests.get(user=user)
                form = forms.AnswerRequestForm(instance=incoming)
                action = "answerrequest"
            except ContactRequest.DoesNotExist:
                form = forms.SendRequestForm(model=ContactRequest)
                action = "sendrequest"
            context["form"] = form
        context["profile_user"] = user
        context["action"] = action
        context["show_form"] = request.GET.get("action")
        context["is_friend"] = request.user in user.contacts.all() or (
            request.user == user and request.GET.get("as", None) == "friend"
        )
        return render(request, self.template_name, context)

    def post(self, request, pk):
        user = User.objects.get(id=pk)
        action = request.POST.get("action")
        if "sendrequest" in request.POST:
            form = forms.SendRequestForm(request.POST, model=ContactRequest)
            if form.is_valid():
                contactrequest = form.save(commit=False)
                contactrequest.user = request.user
                contactrequest.profile = user
                try:
                    contactrequest.save()
                    messages.add_message(request, messages.SUCCESS, _("Request sent"))
                except db.IntegrityError:
                    messages.add_message(
                        request, messages.WARNING, _("Request already sent")
                    )
        elif "cancelrequest" in request.POST:
            try:
                ContactRequest.objects.get(user=request.user, profile=user).delete()
                messages.add_message(request, messages.SUCCESS, _("Request canceled"))
            except ContactRequest.DoesNotExist:
                pass
        elif "acceptrequest" in request.POST:
            try:
                ContactRequest.objects.get(
                    from_user=user, profile=request.user
                ).accept()
                messages.add_message(request, messages.SUCCESS, _("Request accepted"))
            except ContactRequest.DoesNotExist:
                pass
        elif "declinerequest" in request.POST:
            try:
                ContactRequest.objects.get(
                    from_user=user, profile=request.user
                ).decline()
                messages.add_message(request, messages.SUCCESS, _("Request declined"))
            except ContactRequest.DoesNotExist:
                pass
        elif "removecontact" in request.POST:
            request.user.contacts.remove(user)
            messages.add_message(
                request, messages.SUCCESS, _("Contact successfully removed")
            )
        elif "like" in request.POST:
            request.user.activity.get_or_create(
                content_type=ContentType.objects.get_for_model(Profile),
                object_id=user.profile.id,
                activity=Activity.Types.LIKE,
            )
        elif "unlike" in request.POST:
            request.user.activity.filter(
                profile__id=user.profile.id, activity=Activity.Types.LIKE
            ).delete()
        elif "fav" in request.POST:
            request.user.activity.get_or_create(
                content_type=ContentType.objects.get_for_model(Profile),
                object_id=user.profile.id,
                activity=Activity.Types.FAVORITE,
            )
        elif "unfav" in request.POST:
            request.user.activity.filter(
                profile__id=user.profile.id, activity=Activity.Types.FAVORITE
            ).delete()
        elif "sendmessage" in request.POST and user != request.user:
            convo, created = (
                Conversation.objects.filter(users=request.user)
                .filter(users=user)
                .filter(trip=None)
                .get_or_create()
            )
            if created:
                ConversationMembership.objects.create(conversation=convo, user=user)
                ConversationMembership.objects.create(
                    conversation=convo, user=request.user
                )
            return redirect(reverse("messages", args=[convo.id]))
        elif "share" in request.POST:
            form = forms.PostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.shared_object = user.profile
                post.user = request.user
                post.save()
            return redirect(reverse("home"))
        return redirect(request.META.get("HTTP_REFERER"))


class ProfileUpdate(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "profile_edit.html"

    def get(self, request):
        try:
            # Le compteur lié à la page est récupéré et incrémenté
            p = PageNbVisites.objects.get(url=request.path)
            p.nb_visites = F("nb_visites") + 1
            p.save()
        except PageNbVisites.DoesNotExist:
            # Un nouveau compteur à 1 par défaut est créé
            PageNbVisites(url=request.path).save()
        context = self.get_context_data()
        context["nameform"] = forms.NameForm(instance=request.user)
        context["profileform"] = forms.ProfileForm(instance=request.user.profile)
        context["albumform"] = forms.AlbumFormSet(instance=request.user.profile)
        return self.render_to_response(context)

    def post(self, request):
        nameform = forms.NameForm(request.POST, instance=request.user)
        profileform = forms.ProfileForm(
            request.POST, request.FILES, instance=request.user.profile
        )
        albumform = forms.AlbumFormSet(
            request.POST, request.FILES, instance=request.user.profile
        )
        if nameform.is_valid() and profileform.is_valid() and albumform.is_valid():
            nameform.save()
            profileform.save()
            albumform.save()
            message = format_html(
                "<p>{}</p><a href={}>{}</a>",
                _("Profile saved successfully."),
                reverse("profile", args=[request.user.id]),
                _("See your profile"),
            )
            messages.add_message(request, messages.SUCCESS, message)
            return redirect(reverse("profile", args=[request.user.id]))
        else:
            return self.render_to_response(
                {
                    "nameform": nameform,
                    "profileform": profileform,
                    "albumform": albumform,
                }
            )


class ChangeProfileCoverPhotos(ProfileUpdate):
    template_name = "change_profile_cover_photos.html"


class ChangeProfilePhoto(ProfileUpdate):
    template_name = "change-profile-photo.html"


class ContactsView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "contacts.html"

    def get(self, request):
        context = self.get_context_data()
        form = forms.FilterContactForm(request.GET)
        qs = request.user.contacts.all()
        counts = request.user.contacts.values_list("profile__sex").annotate(
            Count("profile__sex")
        )
        context["counts"] = dict(counts)
        if form.is_valid():
            sex = form.cleaned_data.get("sex")
            if sex != "all":
                qs = qs.filter(profile__sex=sex)
            """order = form.cleaned_data.get('order_by')
            if order == 'likes':
                qs.annotate(nb_likes=Count('likes')).order_by('-nb_likes')
            elif order == 'travels':
                qs.annotate(nb_cotravels=Count('trips')).order_by('-nb_cotravels')
            elif order == 'last':
                qs.order_by('trips_last_start')
            elif order == 'next':
                qs.order_by('trips_next_start')"""
        else:
            return redirect("{:s}?sex=all".format(reverse("contacts")))
        context["form"] = form
        context["contacts"] = qs.annotate_for(request.user)
        return self.render_to_response(context)


class RequestsView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "requests.html"

    def get(self, request):  # sourcery skip: avoid-builtin-shadow
        type = request.GET.get("type")
        if type == "contact":
            qs = request.user.requests.all()
        elif type == "trip":
            qs = TripRequest.objects.prefetch_related("trip__members").filter(
                trip__members=request.user
            )
        else:
            return redirect("{:s}?type=contact".format(reverse("requests")))
        context = self.get_context_data()
        context["requests"] = qs
        return self.render_to_response(context)

    def post(self, request):  # sourcery skip: avoid-builtin-shadow
        type = request.GET.get("type")
        action = request.POST.get("action")
        request_id = request.POST.get("request_id")
        if type == "contact":
            req = ContactRequest.objects.get(id=request_id)
        elif type == "trip":
            req = TripRequest.objects.get(id=request_id)
        if action == "accept":
            if type == "contact":
                req.accept()
                message = format_html(
                    "<p>{} {}</p><a href={}>{}</a>",
                    _("You are now friends with "),
                    req.user.get_full_name(),
                    reverse("profile", args=[req.user.id]),
                    _("See profile"),
                )
                messages.add_message(request, messages.SUCCESS, message)
            elif type == "trip":
                req.accept(request.user)
                message = format_html(
                    "<p>{} {}</p><a href={}>{}</a><p>{}</p>",
                    _("You have accepted "),
                    req.user.get_full_name(),
                    reverse("profile", args=[req.user.id]),
                    _("See profile"),
                    _(
                        'Please go to your profile, in the "CoTravels" section, to see your mutual boarding card. You can then share it on your feed, by mail and on all social media.'
                    ),
                )
                messages.add_message(request, messages.SUCCESS, message)
        elif action == "decline":
            req.decline()
            messages.add_message(request, messages.SUCCESS, _("Request declined"))
        return redirect(request.META.get("HTTP_REFERER"))


class SearchView(ContextMixin, TemplateView):
    template_name = "search.html"

    def get(self, request):
        context = self.get_context_data()
        form = forms.SearchForm(request.GET)
        context["form"] = form
        if form.data and form.is_valid():
            search = form.save(commit=False)
            if request.user.is_authenticated:
                search, created = Search.objects.filter(
                    id__in=request.user.searches.all()[:1]
                ).get_or_create(**form.cleaned_data, user=request.user)
                search.save()
            results = User.objects.all()
            keywords = []
            if "nonsmoker" in form.data:
                results = results.filter(profile__smoker=False)
            if "nonsmoker" in form.data:
                results = results.filter(profile__covid=True)
            if "help_ukranian" in form.data:
                results = results.filter(profile__help_ukranian=True)
            if "I_have_an_handicap" in form.data:
                results = results.filter(profile__I_have_an_handicap=True)
            if "sex" in form.data:
                sex = form.cleaned_data["sex"]
                results = results.filter(profile__sex=sex)
                if sex == 0:
                    keywords.append(_("women"))
                else:
                    keywords.append(_("men"))
            else:
                keywords = [_("people")]
            if "lucky" in form.data:
                lucky = form.data["lucky"]
                if lucky == "profile":
                    pf = request.user.profile
                    results = results.filter(
                        profile__level=pf.level,
                        profile__sector=pf.sector,
                        profile__job=pf.job,
                        profile__smoker=pf.smoker,
                    )
                elif lucky == "trip":
                    destinations = City.objects.filter(
                        trips__members=request.user
                    ).distinct()
                    results = (
                        results.filter(trips__destination__in=destinations)
                        .annotate(count=Count("id"))
                        .order_by("-count")
                    )
                elif lucky == "search":
                    last_searches = request.user.searches.all()[:5]
                    results = results.filter(
                        reduce(
                            or_,
                            (
                                Q(
                                    searches__destination=search.destination,
                                    searches__start=search.start,
                                    searches__end=search.end,
                                )
                                for search in last_searches
                            ),
                        )
                    )
            if "minage" in form.data:
                minage = form.cleaned_data["minage"]
                results = results.filter(
                    profile__birthdate__lte=datetime.date.today()
                    - datetime.timedelta(days=minage * 365),
                )
                keywords.append(_("over"), str(minage))
            if "maxage" in form.data:
                maxage = form.cleaned_data["maxage"]
                results = results.filter(
                    profile__birthdate__gte=datetime.date.today()
                    - datetime.timedelta(days=maxage * 365)
                )
                if minage:
                    keywords.append(_("and"))
                keywords.extend([_("under"), str(maxage)])
            if "language" in form.data:
                languages = form.cleaned_data["language"]
                for language in languages:
                    results = results.filter(profile__languages__contains=language)
                keywords.append(_("speaking"))
                joiner = " " + _("and") + " "
                keywords.append(joiner.join(languages))
            if "start" in form.data:
                start = form.cleaned_data["start"]
                end = form.cleaned_data["end"]
                results = results.filter(trips__start__gte=start, trips__end__lte=end)
                if start < datetime.date.today():
                    keywords.append(_("has travelled between"))
                else:
                    keywords.append(_("will travel between"))
                keywords.append(start.strftime("%x"))
                keywords.append(_("and"))
                keywords.append(end.strftime("%x"))
            else:
                results = results.filter(trips__start__gte=datetime.date.today())
                keywords.append(_("will travel"))
            if "destination" in form.data or "country" in form.data:
                keywords.append(_("to"))
                if "destination" in form.data:
                    destination = form.cleaned_data["destination"]
                    context["destination"] = destination
                    results = results.filter(trips__destination=destination)
                    keywords.append(destination.name)
                if "country" in form.data:
                    country = form.cleaned_data["country"]
                    context["destination"] = country
                    results = results.filter(trips__destination__country=country)
                    keywords.append(country.name)
            if "departure" in form.data:
                departure = form.cleaned_data["departure"]
                results = results.filter(trips__departure=departure)
                keywords.extend([_("from"), departure.name])
            if "level" in form.data:
                level = form.cleaned_data["level"]
                results = results.filter(profile__level=level)
            if "subjects" in form.data:
                subjects = form.cleaned_data["subjects"]
                for subject in subjects:
                    results = results.filter(profile__subjects__contains=subject)
            if "sector" in form.data:
                sector = form.cleaned_data["sector"]
                results = results.filter(profile__sector=sector)
            if "job" in form.data:
                job = form.cleaned_data["job"]
                results = results.filter(profile__job=job)
            if "current" in form.data:
                current = form.cleaned_data["current"]
                results = results.filter(profile__current__icontains=current)
            if "previous" in form.data:
                previous = form.cleaned_data["previous"]
                results = results.filter(profile__previous__icontains=previous)

            if "children" in form.data:
                children = form.cleaned_data["children"]
                results = results.filter(profile__children=children)
            if "zodiac" in form.data:
                zodiac = form.cleaned_data["zodiac"]
                results = results.filter_zodiac(zodiac)
            if "personalities" in form.data:
                personalities = form.cleaned_data["personalities"]
                for personality in personalities:
                    results = results.filter(
                        profile__personalities__contains=personality
                    )
            if "hobbies" in form.data:
                hobbies = form.cleaned_data["hobbies"]
                for hobby in hobbies:
                    results = results.filter(profile__hobbies__contains=hobby)
            if "licenses" in form.data:
                licenses = form.cleaned_data["licenses"]
                for license in licenses:
                    results = results.filter(profile__licenses__contains=license)

            results = results.distinct().select_related("profile")

            if request.user.is_authenticated:
                results = results.annotate_for(request.user)
            else:
                for field in form.fields:
                    if field not in ["destination", "start", "end"]:
                        form.fields[field].widget.attrs["disabled"] = True
                results = results[:21]

            advanced = False
            extra = 0
            for data in form.data:
                if data not in ["destination", "country", "departure", "start", "end"]:
                    advanced = True
                elif data not in ["sex", "minage", "maxage", "sex", "language"]:
                    extra += 1
            context["results"] = results
            context["summary"] = " ".join(map(str, keywords))
            context["advanced"] = advanced

        if request.user.is_authenticated:
            near_users = User.objects.filter(
                near(request.user.profile.place, 1)
            ).prefetch_related("profile__place")
            points = [
                (
                    user.profile.place.latitude,
                    user.profile.place.longitude,
                    '<a target="_blank" rel="noopener noreferrer" target="_parent" href={}>{}</a>'.format(
                        reverse("profile", args=[user.id]), _("view profile")
                    ),
                    unidecode.unidecode(user.first_name),
                )
                for user in near_users
            ]
            context["aroundmemap"] = generate_map(points)

        if "destination" in locals():
            near_users = User.objects.filter(near(destination, 1)).prefetch_related(
                "profile__place"
            )
            points = [
                (
                    user.profile.place.latitude,
                    user.profile.place.longitude,
                    '<a target="_blank" rel="noopener noreferrer" target="_parent" href={}>{}</a>'.format(
                        reverse("profile", args=[user.id]), _("view profile")
                    ),
                    unidecode.unidecode(user.first_name),
                )
                for user in near_users
            ]
            context["arounddestmap"] = generate_map(points)

        return self.render_to_response(context)


class FavouritesView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "favourites.html"

    def get(self, request):
        type = request.GET.get("type")

        if type == "following":
            ct = ContentType.objects.get_for_model(Profile)
            pks = Activity.objects.filter(
                activity=Activity.Types.FAVORITE, content_type=ct, user=request.user
            ).values_list("object_id", flat=True)
            qs = User.objects.filter(profile__id__in=pks)
        elif type == "followers":
            pks = Activity.objects.filter(
                activity=Activity.Types.FAVORITE, profile=request.user.profile
            ).values_list("user_id", flat=True)
            qs = User.objects.filter(id__in=pks)
        elif type == "trip-following":
            ct = ContentType.objects.get_for_model(Trip)
            pks = Activity.objects.filter(
                activity=Activity.Types.FAVORITE, content_type=ct, user=request.user
            ).values_list("object_id", flat=True)
            qs = Trip.objects.filter(id__in=pks)
        elif type == "trip-followers":
            pks = Activity.objects.filter(
                activity=Activity.Types.FAVORITE, trip__members=request.user
            ).values_list("user_id", flat=True)
            qs = User.objects.filter(id__in=pks)
        else:
            return redirect("{}?type={}".format(reverse("favourites"), "following"))
        qs = qs.annotate_for(request.user)
        context = self.get_context_data()
        context["favorites"] = qs
        return self.render_to_response(context)


class InviteView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "invite.html"

    def get(self, request):
        try:
            # Le compteur lié à la page est récupéré et incrémenté
            p = PageNbVisites.objects.get(url=request.path)
            p.nb_visites = F("nb_visites") + 1
            p.save()
        except PageNbVisites.DoesNotExist:
            # Un nouveau compteur à 1 par défaut est créé
            PageNbVisites(url=request.path).save()
        context = self.get_context_data()
        context["form"] = forms.InviteFriendForm()
        return self.render_to_response(context)

    def post(self, request):
        context = self.get_context_data()
        form = forms.InviteFriendForm(request.POST)
        if form.is_valid():
            context = {"user": request.user}
            send_mail(
                form.cleaned_data["email"],
                _("Join me on Cogofly."),
                "email-friend-invite.html",
                context,
            )
            messages.add_message(
                request, messages.SUCCESS, _("Invitation successfully sent")
            )
        return self.render_to_response(context)


class ContactUsView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "contact-us.html"

    def get(self, request):
        context = self.get_context_data()
        context["remarkform"] = forms.RemarkForm()
        context["testimonyform"] = forms.TestimonyForm(
            instance=getattr(request.user, "testimony", None)
        )
        return self.render_to_response(context)

    def post(self, request):
        if "testimony" in request.POST:
            form = forms.TestimonyForm(
                request.POST, instance=getattr(request.user, "testimony", None)
            )
            if form.is_valid():
                testimony = form.save(commit=False)
                testimony.accepted = False
                testimony.user = request.user
                testimony.save()
                messages.add_message(request, messages.SUCCESS, _("Testimony saved"))
        elif "delete" in request.POST:
            request.user.testimony.delete()
            messages.add_message(request, messages.SUCCESS, _("Testimony deleted"))
        else:
            form = forms.RemarkForm(request.POST)
            admin = User.objects.get(email=settings.ADMIN_EMAIL)
            if form.is_valid and admin != request.user:
                convo, created = (
                    Conversation.objects.filter(users=request.user)
                    .filter(users=admin)
                    .filter(trip=None)
                    .distinct()
                    .get_or_create()
                )
                if created:
                    ConversationMembership.objects.create(
                        conversation=convo, user=request.user
                    )
                    ConversationMembership.objects.create(
                        conversation=convo, user=admin
                    )
                message = form.save(commit=False)
                message.user = request.user
                message.conversation = convo
                message.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _("Your feedback has been successfully sent"),
                )

                admin.email_user(
                    "New Remark",
                    f"You have a new remark from {request.user}({request.user.email})",
                )
        return redirect(reverse("contact_us"))


class HomeView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "seed-feed.html"

    def get(self, request):
        try:
            # Le compteur lié à la page est récupéré et incrémenté
            p = PageNbVisites.objects.get(url=request.path)
            p.nb_visites = F("nb_visites") + 1
            p.save()
        except PageNbVisites.DoesNotExist:
            # Un nouveau compteur à 1 par défaut est créé
            PageNbVisites(url=request.path).save()
        all_posts = (
            request.user.visible_posts.annotate_for(request.user)
            .prefetch_related(
                Prefetch(
                    "comments", queryset=Comment.objects.annotate_for(request.user)
                ),
                "shared_object",
            )
            .annotate(
                shared_object_is_favorite=Exists(
                    request.user.activity.filter(
                        content_type=OuterRef("content_type"),
                        object_id=OuterRef("object_id"),
                        activity=Activity.Types.FAVORITE,
                    )
                ),
                shared_object_is_liked=Exists(
                    request.user.activity.filter(
                        content_type=OuterRef("content_type"),
                        object_id=OuterRef("object_id"),
                        activity=Activity.Types.LIKE,
                    )
                ),
            )
        )
        paginator = Paginator(all_posts, 10)
        page = request.GET.get("page")
        posts = paginator.get_page(page or 1)
        context = self.get_context_data()
        context.update(
            {
                "trips": Trip.objects,
                "posts": posts,
                "post_form": forms.PostForm(),
                "comment_form": forms.CommentForm(),
                "album_form": forms.PostAlbumFormSet(),
                "last_searches_with_cities": Search.objects.exclude(
                    destination=None
                ).prefetch_related("destination")[:21],
            }
        )
        return self.render_to_response(context)

    def post(self, request):
        if "welcome" in request.POST:
            form = forms.WelcomeMessageForm(request.POST, instance=request.user)
            if form.is_valid():
                form.welcome_message = False
                form.save()
        if "completion" in request.POST:
            form = forms.CompletionMessageForm(request.POST, instance=request.user)
            if form.is_valid():
                form.completion_message = False
                form.save()
        return redirect(reverse("home"))


class PostView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "post-view.html"

    def get(self, request, pk):
        context = super().get_context_data()
        context["post"] = (
            request.user.visible_posts.annotate_for(request.user)
            .prefetch_related(
                Prefetch(
                    "comments",
                    queryset=Comment.objects.all().annotate_for(request.user),
                )
            )
            .get(id=pk)
        )
        context["comment_form"] = forms.CommentForm()
        return self.render_to_response(context)

    def post(self, request, pk=None):
        if pk:
            post = request.user.visible_posts.get(id=pk)
            ct = ContentType.objects.get_for_model(post)
            if "comment" in request.POST:
                form = forms.CommentForm(request.POST)
                if form.is_valid():
                    comment = form.save(commit=False)
                    comment.user = request.user
                    comment.post = post
                    comment.save()
            elif "share" in request.POST:
                form = forms.ShareForm(request.POST)
                if form.is_valid():
                    new_post = form.save(commit=False)
                    new_post.user = request.user
                    new_post.shared_object = post
                    new_post.save()
            elif "like" in request.POST:
                request.user.activity.get_or_create(
                    content_type=ct, object_id=post.id, activity=Activity.Types.LIKE
                )
            elif "unlike" in request.POST:
                request.user.activity.filter(
                    post__id=post.id, activity=Activity.Types.LIKE
                ).delete()
            elif "delete" in request.POST:
                post.delete()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _("Your post has been successfully deleted"),
                )
                return redirect(reverse("home"))
        else:
            form = forms.PostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                post.save()
                albumform = forms.PostAlbumFormSet(
                    request.POST, request.FILES, instance=post
                )
                if albumform.is_valid():
                    albumform.save()
        return redirect("{}#{}".format(request.META.get("HTTP_REFERER"), post.id))


class CommentView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "post.html"

    def post(self, request, pk):
        if "like" in request.POST:
            comment = request.user.visible_comments.get(id=pk)
            request.user.activity.get_or_create(
                content_type=ContentType.objects.get_for_model(comment),
                object_id=comment.id,
                activity=Activity.Types.LIKE,
            )
        elif "unlike" in request.POST:
            comment = request.user.visible_comments.get(id=pk)
            request.user.activity.filter(
                comment__id=comment.id, activity=Activity.Types.LIKE
            ).delete()
        elif "delete" in request.POST:
            comment = request.user.comments.get(id=pk)
            comment.delete()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Your comment has been successfully deleted"),
            )
        return redirect(
            "{}#{}".format(request.META.get("HTTP_REFERER"), comment.post.id)
        )

    """
    def delete(self, request, pk):
        comment = self.user.comments.get(id=pk)
        comment.delete()
        messages.add_message(request, messages.SUCCESS, _('Your comment has been successfully deleted'))
        return redirect(request.META.get('HTTP_REFERER'))
    """


class TripsView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "trip-cards.html"

    def get(self, request):
        type = request.GET.get("type")
        context = self.get_context_data()
        qs = Trip.objects.filter(user=request.user).annotate_for(request.user)
        if type == "future":
            qs = qs.future()
        elif type == "past":
            qs = qs.past()
        elif type == "map":
            points = [
                (
                    trip.destination.latitude,
                    trip.destination.longitude,
                    None,
                    unidecode.unidecode(
                        "{} ({})".format(
                            trip.destination.name,
                            date_format(trip.start, "SHORT_DATE_FORMAT"),
                            date_format(trip.start, "SHORT_DATE_FORMAT"),
                        )
                    ),
                )
                for trip in qs
            ]
            context["map"] = generate_map(points)
        else:
            return redirect("{}?type={}".format(reverse("trips"), "future"))
        context["trips"] = qs
        return self.render_to_response(context)


class CotravelsView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "cotravels.html"

    def get(self, request):  # sourcery skip: avoid-builtin-shadow
        type = request.GET.get("type")
        context = self.get_context_data()
        qs = Trip.objects.annotate_for(request.user).filter(
            members=request.user, members__count__gte=2
        )
        context["cotravels"] = qs
        if type == "wewilldoit":
            qs = qs.future()
        elif type == "wedidit":
            qs = qs.past()
        else:
            return redirect(f'{reverse("cotravels")}?type=wewilldoit')
        context["trips"] = qs
        return self.render_to_response(context)


class MessagesView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "messages.html"

    def get(self, request, pk=None):
        context = {}
        context["convos"] = convos = (
            request.user.conversations.prefetch_related(
                Prefetch("users", queryset=User.objects.exclude(id=request.user.id)),
                "messages",
            )
            .annotate(
                unread=Count(
                    "messages",
                    filter=Q(messages__created__gt=F("membership__last_seen")),
                ),
                order=Max("messages__created"),
            )
            .order_by("order")
        )
        if pk:
            try:
                convo = convos.get(id=pk)
                context["convo"] = convo
            except Conversation.DoesNotExist:
                return redirect("messages")
            ConversationMembership.objects.get(
                user=request.user, conversation=convo
            ).save()  # update last_seen field
            paginator = Paginator(convo.messages.all(), 10)
            page = request.GET.get("page")
            messages = paginator.get_page(page or 1)
            context["chats"] = messages
            context["form"] = forms.MessageForm()
        else:
            try:
                pk = request.user.messages.last().conversation_id
                return redirect(reverse("messages", args=[pk]))
            except:
                convo = Conversation.objects.none()
        context.update(self.get_context_data())
        return self.render_to_response(context)

    def post(self, request, pk):
        convo = Conversation.objects.get(id=pk)
        form = forms.MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = convo
            message.user = request.user
            message.save()
        return redirect(reverse("messages", kwargs={"pk": convo.id}))


class TripView(ProtectedMixin, ContextMixin, TemplateView):
    template_name = "trip.html"

    def get(self, request, pk):
        context = self.get_context_data()
        context["trip"] = (
            Trip.objects.all()
            .annotate_for(request.user)
            .prefetch_related(
                "pictures",
                "destination",
                Prefetch(
                    "members", queryset=User.objects.all().annotate_for(request.user)
                ),
            )
            .get(id=pk)
        )
        context["sendrequestform"] = forms.SendRequestForm(model=TripRequest)
        context["show_form"] = request.GET.get("action")
        return self.render_to_response(context)

    def post(self, request, pk):
        trip = Trip.objects.get(id=pk)
        context = self.get_context_data()
        if "like" in request.POST:
            request.user.activity.get_or_create(
                content_type=ContentType.objects.get_for_model(trip),
                object_id=trip.id,
                activity=Activity.Types.LIKE,
            )
        elif "unlike" in request.POST:
            request.user.activity.filter(
                trip__id=trip.id, activity=Activity.Types.LIKE
            ).delete()
        elif "fav" in request.POST:
            request.user.activity.get_or_create(
                content_type=ContentType.objects.get_for_model(trip),
                object_id=trip.id,
                activity=Activity.Types.FAVORITE,
            )
        elif "unfav" in request.POST:
            request.user.activity.filter(
                trip__id=trip.id, activity=Activity.Types.FAVORITE
            ).delete()
        elif "sendrequest" in request.POST:
            form = forms.SendRequestForm(request.POST, model=TripRequest)
            if form.is_valid():
                triprequest = form.save(commit=False)
                triprequest.user = request.user
                triprequest.trip = trip
                triprequest.save()
                messages.add_message(request, messages.SUCCESS, _("Request sent"))
            else:
                messages.add_message(request, messages.ERROR, _("Error"))
        elif "cancelrequest" in request.POST:
            try:
                TripRequest.objects.get(user=request.user, trip=trip).delete()
                messages.add_message(request, messages.SUCCESS, _("Request canceled"))
            except TripRequest.DoesNotExist:
                messages.add_message(
                    request, messages.INFO, _("There is no request for this trip")
                )
        elif "leavetrip" in request.POST:
            trip.remove(request.user)
            message = _("You have been removed from this trip")
            messages.add_message(request, messages.SUCCESS, message)
        elif "delete" in request.POST:
            trip = request.user.own_trips.get(id=pk)
            trip.delete()
            message = _("Your trip has been deleted")
            messages.add_message(request, messages.SUCCESS, message)
            return redirect(reverse("trips"))
        elif "share" in request.POST:
            form = forms.PostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.shared_object = trip
                post.user = request.user
                post.save()
                messages.add_message(request, messages.SUCCESS, _("Trip shared"))
            else:
                messages.add_message(request, messages.ERROR, _("Error"))
            return redirect(reverse("home"))
        elif "email_share" in request.POST:
            form = forms.EmailShareForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data["email"]
                context = {
                    "user": request.user,
                    "trip": trip,
                    "text": form.cleaned_data["text"],
                }
                send_mail(
                    email, _("Join my trip on Cogofly"), "email-share.html", context
                )
                messages.add_message(
                    request, messages.SUCCESS, _("Trip shared via email")
                )
            elif "email" in form.errors:
                messages.add_message(request, messages.ERROR, _("Wrong email adress"))
        return redirect(request.META.get("HTTP_REFERER"))


class TripEditView(ContextMixin, TemplateView):
    template_name = "trip_edit.html"

    def get(self, request, pk=None):
        context = self.get_context_data()
        trip = context["trip"] = Trip.objects.get(id=pk) if pk else None
        context["form"] = forms.TripForm(instance=trip)
        context["albumform"] = forms.TripAlbumFormSet(instance=trip)
        return self.render_to_response(context)

    def post(self, request, pk=None):
        context = self.get_context_data()
        if "load" in request.POST:
            context["form"] = forms.TripForm(json.loads(request.session["trip"]))
            context["albumform"] = forms.TripAlbumFormSet()
            del request.session["trip"]
            return self.render_to_response(context)
        elif "forget" in request.POST:
            del request.session["trip"]
            return redirect(reverse("trip_add"))
        trip = Trip.objects.get(id=pk) if pk else None
        form = context["form"] = forms.TripForm(request.POST, instance=trip)
        albumform = context["albumform"] = forms.TripAlbumFormSet(
            request.POST, request.FILES, instance=trip
        )
        if "save" in request.POST:
            return redirect(reverse("trips"))
        elif form.is_valid():
            context["preview"] = True
            trip = context["trip"] = form.save(commit=False)
            if request.user.is_authenticated:
                trip.user = request.user
                trip.save()
                trip.members.add(request.user)
                if not pk:
                    convo, _ = Conversation.objects.get_or_create(trip=trip)
                    ConversationMembership.objects.create(
                        conversation=convo, user=request.user
                    )
                albumform = forms.TripAlbumFormSet(
                    request.POST, request.FILES, instance=trip
                )
                context["albumform"] = albumform
                if albumform.is_valid():
                    albumform.save()
            else:
                request.session["trip"] = json.dumps(
                    {
                        key: form.data[key]
                        for key in ("start", "end", "destination", "comment")
                    }
                )
        return self.render_to_response(context)


class NotificationView(ProtectedMixin, ContextMixin, View):
    def get(self, request, pk):
        notification = request.user.notifications.get(id=pk)
        notification.read = True
        notification.save()
        return redirect(notification.target.get_absolute_url())


class CityAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = City.objects.order_by("-population")

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class CountryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Country.objects.none()

        qs = Country.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class ContactAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return User.objects.none()

        qs = self.request.user.contacts.order_by("first_name")

        if self.q:
            qs = qs.filter(first_name__istartswith=self.q)

        return qs


class UkraineView(TemplateView):
    template_name = "ukraine.html"
