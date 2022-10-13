from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _
from django.utils.html import mark_safe, escape
from django.urls import reverse
from django.http import HttpResponse

from .models import *
from social_django.models import UserSocialAuth
import csv
from functools import reduce


def export_as_csv_action(description="Export selected objects as CSV file", fields=None, exclude=None, header=True):
    def export_as_csv(modeladmin, request, queryset):
        opts = modeladmin.model._meta
        field_names = {field.name for field in opts.fields}

        if fields:
            fieldset = set(fields)
            field_names = field_names & fieldset

        elif exclude:
            excludeset = set(exclude)
            field_names = field_names - excludeset

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(
            opts)

        writer = csv.writer(response)

        if header:
            writer.writerow(list(field_names))
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = description
    return export_as_csv


class DynamicLookupMixin(object):
    '''
    a mixin to add dynamic callable attributes like 'book__author' which
    return a function that return the instance.book.author value
    '''

    def __getattr__(self, attr):
        if ('__' in attr
            and not attr.startswith('_')
            and not attr.endswith('_boolean')
                and not attr.endswith('_short_description')):

            def dyn_lookup(instance):
                # traverse all __ lookups
                return reduce(lambda parent, child: getattr(parent, child),
                              attr.split('__'),
                              instance)

            # get admin_order_field, boolean and short_description
            dyn_lookup.admin_order_field = attr
            dyn_lookup.boolean = getattr(
                self, '{}_boolean'.format(attr), False)
            dyn_lookup.short_description = getattr(
                self, '{}_short_description'.format(attr),
                attr.replace('_', ' ').capitalize())

            return dyn_lookup

        # not dynamic lookup, default behaviour
        return self.__getattribute__(attr)


class SocialAuthInline(admin.TabularInline):
    model = UserSocialAuth
    readonly_fields = ('provider', 'uid', 'extra_data')
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    model = Profile
    can_delete = True
    fk_name = 'user'
    list_display = ('user', 'email')
    readonly_fields = ('place','birthplace', 'nationality', 'mothertongue', 'languages', 'level', 'subjects', 'sector', 'job', 'current', 'previous',
        'personalities', 'hobbies', 'licenses', 'how', )

class ProfileInline(admin.StackedInline):
    model = Profile
    fields = ('birthdate',)


def approve_testimony(modeladmin, request, queryset):
    queryset.update(accepted=True)


approve_testimony.short_description = _('Accept selected testimonies')


@admin.register(Testimony)
class TestimonyAdmin(admin.ModelAdmin):
    model = Testimony
    can_delete = True
    list_display = ('text', 'user', 'accepted', 'created')
    readonly_fields = ('user', 'created', 'text')
    fk_name = 'text'
    actions = [approve_testimony]


@admin.register(User)
class UserAdmin(DjangoUserAdmin, DynamicLookupMixin):
    inlines = [SocialAuthInline, ProfileInline]
    fieldsets = (
        (None, {'fields': ('email', 'password',)}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),


    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2',),
        }),
    )
    list_display = ('email', 'first_name', 'last_name',
                    'is_staff', 'profile_link', 'profile__birthdate')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    ordering = ('email',)
    actions = [
        export_as_csv_action("Export selected objects as CSV file", fields=[
            'last_login',
            'profile__sex',
        ])
    ]

    def profile_link(self, obj):
        link = reverse("admin:cogofly_profile_change", args=[obj.profile.id])
        return mark_safe(f'<a href="{link}">{escape(obj.profile.__str__())}</a>')

    def get_queryset(self, request):
        qs = self.model._base_manager.get_queryset()
        if ordering := self.get_ordering(request):
            qs = qs.order_by(*ordering)
        return qs

from django import forms


class UserManyToManyForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserManyToManyForm, self).__init__(*args, **kwargs)
        self.fields['members'].queryset = User.objects.all()
        
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    # model = Trip
    form=UserManyToManyForm
    raw_id_fields = ('destination', 'departure', 'user')
    filter_horizontal = ('members',)
    search_fields = ('destination__display_name',)

#@admin.register(Trip)
#class TripAdmin(admin.ModelAdmin):
#    model = Trip
#    raw_id_fields = ('destination', 'departure', 'user')
