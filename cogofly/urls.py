from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.conf import settings

from .forms import InactiveUsersPasswordResetForm
from . import views

urlpatterns = [
    path('', views.landing, name="landing"),
    path('about-us', views.AboutUsView.as_view(), name="about-us"),
    path('the-team', views.TeamView.as_view(), name="the-team"),
    path('contact-cogofly', views.ContactUsView.as_view(), name="contact-cogofly"),
    path('testimonies', views.TestimonyView.as_view(), name="testimonies"),
    path('blog', views.BlogView.as_view(), name="blog"),
    path('terms-and-conditions', views.TermsConditionsView.as_view(), name="terms-and-conditions"),
    path('privacy-policy', views.PrivacyPolicyView.as_view(), name="privacy-policy"),

    path('how-it-works', TemplateView.as_view(template_name='how-it-works.html'), name="howitworks"),
    path('data-deletion-instructions', views.DataDeletionInstructions.as_view(), name="datadeletionsinstructions"),   
    path('covid-19', views.Covid.as_view(), name="covid"),

    path('signup', views.signup, name="signup"),
    path('signup/next', views.signup_next, name='signup-next'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),

    path('login', views.CustomLoginView.as_view(), name="login"),
    path('logout', auth_views.LogoutView.as_view(template_name='logout.html'), name="logout"),

    path('password/reset', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html',
        subject_template_name='password_reset_subject.txt',
        html_email_template_name = 'password_reset_email.html',
        from_email = settings.DEFAULT_FROM_EMAIL,
        form_class = InactiveUsersPasswordResetForm
    ), name='password_reset'),
    path('password/reset/done', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>', views.InactiveUsersPasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('password/reset/confirm', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

    path('home', views.HomeView.as_view(), name='home'),
    path('post/', views.PostView.as_view(), name='post'),
    path('post/<int:pk>', views.PostView.as_view(), name='post'),
    path('comment/<int:pk>', views.CommentView.as_view(), name='comment'),

    path('account', views.account, name='account'),

    path('notification/<int:pk>', views.NotificationView.as_view(), name='notification'),

    path('profile/edit', views.ProfileUpdate.as_view(), name='profile_edit'),
    path('profile/<int:pk>', views.ProfileView.as_view(), name='profile'),
    #path('seed-feed', views.seed_feed, name="seed-feed"),

    path('search', views.SearchView.as_view(), name='search'),
    path('invite', views.InviteView.as_view(), name='invite'),
    path('contact_us', views.ContactUsView.as_view(), name='contact_us'),

    path('requests', views.RequestsView.as_view(), name='requests'),
    path('contacts', views.ContactsView.as_view(), name='contacts'),
    path('favourites', views.FavouritesView.as_view(), name="favourites"),
    path('messages', views.MessagesView.as_view(), name='messages'),
    path('messages/<int:pk>', views.MessagesView.as_view(), name='messages'),
    path('trips', views.TripsView.as_view(), name="trips"),
    path('cotravels', views.CotravelsView.as_view(), name='cotravels'),
    path('trip/add', views.TripEditView.as_view(), name="trip_add"),
    path('trip/<int:pk>', views.TripView.as_view(), name="trip"),
    path('trip/<int:pk>/edit', views.TripEditView.as_view(), name="trip_edit"),
    path('trip/<int:pk>/preview', views.TripEditView.as_view(), name="trip-preview"),

    path('city-autocomplete', views.CityAutocomplete.as_view(), name='city-autocomplete'),
    path('country-autocomplete', views.CountryAutocomplete.as_view(), name='country-autocomplete'),
    path('contact-autocomplete', views.ContactAutocomplete.as_view(), name='contact-autocomplete'),
    path('change-profile-photos', views.ChangeProfileCoverPhotos.as_view(), name='change-profile-photos'),
    path('change-profile-photo', views.ChangeProfilePhoto.as_view(), name='change-profile-photo'),
    path('ukraine', views.UkraineView.as_view(), name='ukraine'),
]
