import datetime

from django import forms
from django.contrib.contenttypes.forms import generic_inlineformset_factory
from django.contrib.auth.forms import (
    PasswordChangeForm,
    SetPasswordForm,
    UserCreationForm,
    PasswordResetForm,
    _unicode_ci_compare,
)
from django.forms.widgets import NullBooleanSelect
from django.utils.translation import ugettext_lazy as _
from django.utils import html
from django.utils.safestring import mark_safe

from dal import autocomplete
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Invisible

from .models import *


class SubmitButtonWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        return '<input type="submit" name="%s" value="%s">' % (
            html.escape(name),
            html.escape(value),
        )


class BirthDateInput(forms.DateInput):
    input_type = "date"
    MIN_AGE = 18

    def build_attrs(self, base_attrs, extra_attrs=None):
        max_date = datetime.date.today()
        try:
            max_date = max_date.replace(year=max_date.year - self.MIN_AGE)
        except ValueError:
            max_date = max_date.replace(
                year=max_date.year - self.MIN_AGE, day=max_date.day - 1
            )
        extra_attrs["max"] = max_date
        extra_attrs[
            "oninput"
        ] = "this.setCustomValidity(validity.rangeOverflow ? '{:}' : '')".format(
            _("You must be an adult.")
        )
        return super().build_attrs(base_attrs, extra_attrs)


class SubmitButtonField(forms.Field):
    def __init__(self, *args, **kwargs):
        kwargs["widget"] = SubmitButtonWidget()
        super().__init__(label="", *args, **kwargs)

    def clean(self, value):
        return value


class PictureWidget(forms.ClearableFileInput):
    template_name = "widgets/picture_widget.html"

    def __init__(self, attrs=None):
        default_attrs = {"accept": "image/*"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class AlbumWidget(forms.ClearableFileInput):
    template_name = "widgets/album_widget.html"

    def __init__(self, attrs=None):
        default_attrs = {"accept": "image/*"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class RangeInput(forms.NumberInput):
    input_type = "range"


class BaseForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(label_suffix="", *args, **kwargs)


class BaseModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(label_suffix="", *args, **kwargs)


from django_password_strength.widgets import PasswordStrengthInput


class PasswordStrengthShowInput(PasswordStrengthInput):
    def render(self, name, value, **kwargs):
        show_password_markup = """
        <div class="show-password-input">
            <label for="show-password">%s</label>
            <input type="checkbox" id="show-password" onclick="
            password_inputs = $(this).parent().parent().children('input[type=password], input[type=text]');
            for (i = 0; i < password_inputs.length; i++){
                pass = $('#'.concat(password_inputs[i].id));
                pass.attr('type', (pass.attr('type') == 'text') ? 'password' : 'text')
            };            
            ">                  
        </div>
        """ % (
            _("Show password")
        )
        # pass = $('#id_%s');pass.attr('type', (pass.attr('type') == 'text') ? 'password' : 'text');
        return mark_safe(super().render(name, value, **kwargs) + show_password_markup)


class SetPasswordShowForm(SetPasswordForm):
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=PasswordStrengthShowInput(attrs={"autocomplete": "new-password"}),
    )
    # new_password2 = None


class PasswordChangeShowForm(PasswordChangeForm):
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=PasswordStrengthShowInput(attrs={"autocomplete": "new-password"}),
    )
    # new_password2 = None
    # old_password = None


class InactiveUsersPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        users = User._base_manager.filter(email__iexact=email)
        return (
            u
            for u in users
            if u.has_usable_password()
            and _unicode_ci_compare(email, getattr(u, "email"))
        )


class EmailCheckMixin:
    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User._base_manager.get(email=email)
        except User.DoesNotExist:
            return email

        raise forms.ValidationError(self.unique_email_error)


class SignUpForm(EmailCheckMixin, UserCreationForm):

    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible, label=False)
    password2 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=PasswordStrengthShowInput(
            attrs={"autocomplete": "new-password", "data-toggle": "password"}
        ),
    )
    password1 = forms.CharField(required=False)

    unique_email_error = _(
        mark_safe(
            "The given email is already registered.<br> <a href='/login'>Login</a> or <a href='/password/reset'> reset your password</a>."
        )
    )

    def _clean_fields(self):
        super()._clean_fields()
        self.cleaned_data["password1"] = self.cleaned_data["password2"]

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class NameForm(BaseModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")


class EmailForm(BaseModelForm):
    unique_email_error = _("This email adress is already in use")

    class Meta:
        model = User
        fields = ("email",)


class FrequencyForm(BaseModelForm):
    class Meta:
        model = User
        fields = ("notification_frequency",)


class ChangeEmailForm(EmailCheckMixin, BaseModelForm):
    class Meta:
        model = Profile
        fields = ("email",)


class BlankNullBooleanSelect(NullBooleanSelect):
    def __init__(self, attrs=None):
        choices = (
            ("unknown", ""),
            ("true", _("Yes")),
            ("false", _("No")),
        )
        super(NullBooleanSelect, self).__init__(attrs, choices)


class ProfileForm(BaseModelForm):
    class Meta:
        model = Profile
        exclude = ("user", "privacy", "email")
        widgets = {
            "birthdate": BirthDateInput(format="%Y-%m-%d"),
            "place": autocomplete.ModelSelect2(url="city-autocomplete"),
            "birthplace": autocomplete.ModelSelect2(url="city-autocomplete"),
            "nationality": autocomplete.ModelSelect2(url="country-autocomplete"),
            "mothertongue": autocomplete.Select2Multiple(),
            "languages": autocomplete.Select2Multiple(),
            "level": autocomplete.Select2(),
            "subjects": autocomplete.Select2Multiple(),
            "sectors": autocomplete.Select2Multiple(),
            "job": autocomplete.Select2(),
            "current": autocomplete.Select2(),
            "previous": autocomplete.Select2(),
            "hobbies": autocomplete.Select2Multiple(),
            "personalities": autocomplete.Select2Multiple(),
            "licenses": autocomplete.Select2Multiple(),
            "picture": PictureWidget(),
            "cover": PictureWidget(),
            "covid": BlankNullBooleanSelect(),
            "help ukranians": BlankNullBooleanSelect(),
            "handicap": BlankNullBooleanSelect(),
            "smoker": BlankNullBooleanSelect(),
        }
        help_texts = {
            "birthdate": _("Required"),
            "place": _("Required"),
            "sex": _("Required"),
        }

    def clean_birthdate(self):
        today = datetime.date.today()
        birthdate = self.cleaned_data["birthdate"]
        if (
            today.year
            - birthdate.year
            - ((today.month, today.day) < (birthdate.month, birthdate.day))
            < 18
        ):
            raise forms.ValidationError(_("You must be an adult."))
        return birthdate


invite_text = "Hi,\n\
\n\
Join me absolutely free on, www.cogofly.com, the new community where you can find people you can trust and never have to worry about travelling alone again.\n\
\n\
Don't stay on your own...meet people close to home or abroad and share your activities with them.\n\
\n\
Weekends away, days out, even business trips…you can envisage doing all of these with someone who potentially shares the same socio-professional criteria, hobbies and travel aspirations as you.\n\
\n\
If you enjoy spending time on your own…you will no doubt be inspired by other people’s experiences and be able to share information via this new web platform... and why not make the most of people’s recommendations.\n\
\n\
Cogofly Team: Alone, we think...Together, we get away!\n\
\n\
PS: Once you’ve checked out the site and finalized your subscription, please feel free to share this information with, maybe, your entourage."


class InviteFriendForm(BaseForm):
    email = forms.EmailField()
    text = forms.CharField(initial=invite_text, widget=forms.Textarea())


class EmailShareForm(BaseForm):
    email = forms.EmailField(
        widget=forms.TextInput(attrs={"placeholder": _("Add a mail…")})
    )
    text = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": _("Talk about your trips, past and future ones...")}
        )
    )
    email_share = SubmitButtonField(initial=_("Send"))


class FilterContactForm(forms.Form):
    EMPTY_SEX_CHOICES = [("all", _("All"))] + Profile.SEX_CHOICES
    sex = forms.ChoiceField(choices=EMPTY_SEX_CHOICES)
    """min_age = forms.IntegerField(required=False, widget=RangeInput(), min_value=18, max_value=99)
    max_age = forms.IntegerField(required=False, widget=RangeInput(), min_value=18, max_value=99)
    order_by = forms.ChoiceField(
        required=False,
        choices=[
            ('dist', _('Distance')),
            ('cotravels', _('Number of Cotravels')),
            ('likes', _('Number of Likes')),
        ]
    )
    mothertongue = forms.ChoiceField(required=False, widget=autocomplete.Select2Multiple(url='language-autocomplete'))"""


AlbumFormSet = generic_inlineformset_factory(
    Picture,
    fields=("picture",),
    max_num=6,
    extra=6,
    validate_max=True,
)

TripAlbumFormSet = generic_inlineformset_factory(
    Picture,
    fields=("picture",),
    max_num=21,
    extra=1,
    validate_max=True,
)

PostAlbumFormSet = generic_inlineformset_factory(
    Picture,
    fields=("picture",),
    extra=1,
    max_num=21,
    validate_max=True,
)


def SendRequestForm(*args, **kwargs):
    class SendRequestForm(forms.ModelForm):
        sendrequest = SubmitButtonField(initial=_("Send request"))

        class Meta:
            model = kwargs.pop("model")
            fields = ("message",)

    return SendRequestForm(*args, **kwargs)


class TripRequestForm(BaseModelForm):
    sendrequest = SubmitButtonField(initial=_("Send contact request"))

    class Meta:
        model = ContactRequest
        fields = ("message",)


class AnswerRequestForm(BaseModelForm):
    acceptrequest = SubmitButtonField(initial=_("Accept"))
    declinerequest = SubmitButtonField(initial=_("Decline"))

    class Meta:
        model = ContactRequest
        fields = ("message",)
        widgets = {"message": forms.TextInput(attrs={"readonly": ""})}


class TripForm(BaseModelForm):
    class Meta:
        model = Trip
        exclude = ("user", "members")
        widgets = {
            "departure": autocomplete.ModelSelect2(url="city-autocomplete"),
            "destination": autocomplete.ModelSelect2(url="city-autocomplete"),
            "start": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "end": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "users": autocomplete.ModelSelect2Multiple(url="contact-autocomplete"),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        if end < start:
            self.add_error("end", _("The return date must be after the departure date"))
        departure = cleaned_data.get("departure")
        destination = cleaned_data.get("destination")
        if departure == destination:
            self.add_error(
                "departure",
                _("The departure city must be different from the destination city."),
            )
        return self.cleaned_data


class MessageForm(BaseModelForm):
    class Meta:
        model = Message
        fields = ("text",)


class SearchForm(BaseModelForm):
    class Meta:
        model = Search
        exclude = ("id", "user", "created")
        widgets = {
            "destination": autocomplete.ModelSelect2(url="city-autocomplete"),
            "departure": autocomplete.ModelSelect2(url="city-autocomplete"),
            "country": autocomplete.ModelSelect2(url="country-autocomplete"),
            "start": forms.DateInput(attrs={"type": "date"}),
            "end": forms.DateInput(attrs={"type": "date"}),
            "language": autocomplete.Select2Multiple(),
            "minage": forms.HiddenInput(),
            "maxage": forms.HiddenInput(),
            "level": autocomplete.Select2(
                attrs={"data-minimum-results-for-search": "Infinity"}
            ),
            "subjects": autocomplete.Select2Multiple(),
            "sector": autocomplete.Select2(
                attrs={"data-minimum-results-for-search": "Infinity"}
            ),
            "job": autocomplete.Select2(
                attrs={"data-minimum-results-for-search": "Infinity"}
            ),
            "current": autocomplete.Select2(),
            "previous": autocomplete.Select2(),
            "hobbies": autocomplete.Select2Multiple(),
            "zodiac": autocomplete.Select2(
                attrs={"data-minimum-results-for-search": "Infinity"}
            ),
            "personalities": autocomplete.Select2Multiple(),
            "licenses": autocomplete.Select2Multiple(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        destination = cleaned_data.get("destination")
        country = cleaned_data.get("country")

        if bool(start) != bool(end):
            raise forms.ValidationError(
                _("You must specify a start and end date or any")
            )
        if not start and not destination and not country:
            raise forms.ValidationError(
                _(
                    "CoGoFly only allows you to search trips into the past or future.\n The advanced search will enable you to fine-tune your search to find people like you, but only after at least indicating destination and/or dates."
                )
            )
        elif start and end < start:
            self.add_error("end", _("The return date must be after the departure date"))


class PostForm(BaseModelForm):
    class Meta:
        model = Post
        fields = ("text",)
        help_texts = {"text": _("URLs must start with http or www to be detected")}
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "placeholder": _("Talk about your trips, past and future ones...")
                }
            )
        }


class ShareForm(PostForm):
    share = SubmitButtonField(initial=_("Share on Seed Feed"))


class CommentForm(BaseModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        help_texts = {"text": _("URLs must start with http or www to be detected")}


class DeleteAccountForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(),
        required=False,
        label=_(
            "In order to help us improving Cogofly, and add new features, could you please precise us the reason?"
        ),
    )
    delete = forms.BooleanField(label=_("Do you still agree ?"))


class DeactivateAccountForm(forms.Form):
    deactivate = forms.BooleanField(label=_("Do you still agree ?"))


class PrivacyForm(forms.ModelForm):
    class Meta:
        model = Privacy
        exclude = ("user",)


class RemarkForm(BaseModelForm):
    class Meta:
        model = Message
        fields = ("text",)
        widgets = {"text": forms.Textarea}
        labels = {"text": _("Your message")}


class TestimonyForm(BaseModelForm):
    class Meta:
        model = Testimony
        fields = ("text",)
        labels = {"text": _("Your testimony")}


class WelcomeMessageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("welcome_message",)


class CompletionMessageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("completion_message",)
