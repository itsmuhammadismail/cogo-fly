import datetime
import requests
import uuid
import json
from bisect import bisect

from django.db import models
from django.db.models import F, Q, Count, Exists, OuterRef
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import ngettext_lazy, ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.templatetags.static import static
from django.conf.locale import LANG_INFO

from cities_light.abstract_models import AbstractCity, AbstractRegion, AbstractCountry
from cities_light.receivers import connect_default_signals
from multiselectfield import MultiSelectField

ZODIAC_SIGNS = [
    (1, 20, 0),
    (2, 18, 1),
    (3, 20, 2),
    (4, 20, 3),
    (5, 21, 4),
    (6, 21, 5),
    (7, 22, 6),
    (8, 23, 7),
    (9, 23, 8),
    (10, 23, 9),
    (11, 22, 10),
    (12, 22, 11),
    (12, 31, 0),
]

ZODIAC_NAMES = [
    (0, _("Capricorn")),
    (1, _("Aquarius")),
    (2, _("Pisces")),
    (3, _("Aries")),
    (4, _("Taurus")),
    (5, _("Gemini")),
    (6, _("Cancer")),
    (7, _("Leo")),
    (8, _("Virgo")),
    (9, _("Libra")),
    (10, _("Scorpio")),
    (11, _("Sagittarius")),
]

COMPANIES = list(enumerate(open("companies.txt")))


class Country(AbstractCountry):
    import csv

    currencies = {
        row[1]: row[3]
        for row in csv.reader(open("country-code-to-currency-code-mapping.csv"))
    }

    @property
    def currency(self):
        return self.currencies[self.code2]


connect_default_signals(Country)


class Region(AbstractRegion):
    pass


connect_default_signals(Region)


class City(AbstractCity):
    picture = models.TextField(null=True, blank=True)

    @property
    def picture_urls(self):
        if self.picture:
            picture = json.loads(self.picture)
        else:
            try:
                res = requests.get(
                    f"https://api.teleport.org/api/cities/geonameid:{self.geoname_id}/?embed=city:urban_area/ua:images"
                ).json()
                picture = (
                    res["_embedded"]["city:urban_area"]["_embedded"]["ua:images"][
                        "photos"
                    ][0]["image"]
                    if "_embedded" in res
                    else None
                )
            except:
                picture = None
            self.picture = json.dumps(picture)
            self.save()
        return picture


connect_default_signals(City)


class UserQueryset(models.QuerySet):
    def annotate_for(self, user):
        return self.annotate(
            is_favorite=Exists(
                user.activity.filter(
                    profile=OuterRef("profile"), activity=Activity.Types.FAVORITE
                )
            ),
            is_liked=Exists(
                user.activity.filter(
                    profile=OuterRef("profile"), activity=Activity.Types.LIKE
                )
            ),
        )

    def filter_zodiac(self, zodiac):
        dates = (ZODIAC_SIGNS[zodiac - 1], ZODIAC_SIGNS[zodiac])
        return self.filter(
            Q(
                profile__birthdate__month=dates[0][0],
                profile__birthdate__day__gt=dates[0][1],
            )
            | Q(
                profile__birthdate__month=dates[1][0],
                profile__birthdate__day__lte=dates[1][1],
            )
        )


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_queryset(self):
        return UserQueryset(self.model, using=self._db).filter(is_active=True)

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    username = None
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(_("email address"), unique=True, null=True)

    contacts = models.ManyToManyField("self", symmetrical=True, related_name="+")
    views = models.ManyToManyField("self", symmetrical=False, related_name="visits")

    mentions = GenericRelation("Post", related_query_name="shared_user")
    targeted_notifications = GenericRelation("Notification")

    on_line = models.BooleanField(default=False)
    created = models.DateField(auto_now_add=True)

    class Frequencies(models.IntegerChoices):
        NEVER = 0, _("Never")
        DAILY = 1, _("Daily")
        WEEKLY = 2, _("Weekly")
        MONTHLY = 3, _("Monthly")

    notification_frequency = models.IntegerField(
        _("notification frequency"), choices=Frequencies.choices, default=0
    )

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("profile", kwargs={"pk": self.pk})

    def get_full_name(self):
        return super().get_full_name() if self.is_active else "Deleted user"

    def get_notifications_numbers(self):
        return {
            "unread_messages": ConversationMembership.objects.filter(
                user=self, conversation__messages__created__gt=F("last_seen")
            ).count(),
            "contact_requests": self.requests.count(),
            "trip_requests": self.trips.aggregate(count=Count("requests")).get("count"),
            "notifications": self.notifications.filter(read=False).count(),
        }

    def can_see(self, user, info):
        is_friend = self in user.contacts.all()
        return user[info] and (
            user.privacy[info] == 2 or (user.privacy[info] == 1 and is_friend)
        )

    @property
    def visible_posts(self):
        return Post.objects.filter(user__in=self.contacts.all()) | self.posts.all()

    @property
    def visible_comments(self):
        return Comment.objects.filter(post__in=self.visible_posts)

    def save(self, *args, **kwargs):
        created = not self.pk
        super().save(*args, **kwargs)
        if created:
            Privacy.objects.create(user=self)

    welcome_message = models.BooleanField(default=True)

    completion_message = models.BooleanField(default=True)


def get_random_path(instance, filename):
    ext = filename.split(".")[-1]
    random = uuid.uuid4()
    return "{:}.{:s}".format(random, ext)


class Profile(models.Model):
    SEX_CHOICES = [(0, _("Female")), (1, _("Male")), (2, _("Other"))]
    HOW_CHOICES = [
        (0, _("Facebook")),
        (1, _("Google")),
        (3, _("Twitter")),
        (4, _("Other social media")),
        (5, _("Flyers")),
        (6, _("Word of mouth")),
    ]
    LEVELS = [
        (0, _("Nursery school")),
        (1, _("Primary education")),
        (2, _("Lower secondary education")),
        (3, _("Upper secondary education")),
        (4, _("Post-secondary non-tertiary education")),
        (5, _("Short-cycle tertiary education")),
        (6, _("Bachelor's Degree or equivalent level")),
        (7, _("Master's Degree or equivalent level")),
        (8, _("Ph.D. or equivalent level")),
        (9, _("Other")),
    ]
    SUBJECTS = [
        (0, _("Agriculture - Forestry - Fisheries")),
        (1, _("Arts - Humanities")),
        (2, _("Business - Administration - Law")),
        (3, _("Education")),
        (4, _("Engineering - Manufacturing - Construction")),
        (5, _("Health - Welfare")),
        (6, _("Informatics - Communication")),
        (7, _("Natural sciences - Mathematics - Statistics")),
        (8, _("Services")),
        (9, _("Social sciences - Journalism - Information")),
        (10, _("Other")),
    ]
    SECTORS = [
        (0, _("Administration")),
        (1, _("Advice - Services - Sales")),
        (2, _("Aeronautics - Space - Defence - Navy - Armament")),
        (3, _("Art - Shows - Creation")),
        (4, _("Associations - Social")),
        (5, _("Audiovisual - Cinema")),
        (6, _("Audit - Accounting - Management - Finance")),
        (7, _("Automobile")),
        (8, _("Banking - Insurance")),
        (9, _("Building - Public maintenance")),
        (10, _("Civil Service")),
        (11, _("Commerce - Distribution")),
        (12, _("Consumer goods - Craft")),
        (13, _("Documentation - Library")),
        (14, _("Environment - Humanitarian work")),
        (15, _("Fairs - Trade fairs - Congresses")),
        (16, _("Fashion - Textiles")),
        (17, _("Food - Catering")),
        (18, _("Funeral Services")),
        (19, _("Hotel - Catering")),
        (20, _("Human Resources")),
        (21, _("IT - Web - Telecommunications - High-Tech")),
        (22, _("Industry - Sciences")),
        (23, _("Languages - Writing - Media")),
        (24, _("Maintenance - Security")),
        (25, _("Marketing - Communication - Advertising")),
        (26, _("Pharmaceuticals - Paramedical - Health - Medical")),
        (27, _("Politics")),
        (28, _("Printing - Editing - Books - Journalism")),
        (29, _("Psychology")),
        (30, _("Real Estate - Culture - Heritage")),
        (31, _("Sport")),
        (32, _("Teaching - Research - Law")),
        (33, _("Tourism")),
        (34, _("Transport - Logistics - Rail")),
        (35, _("Other")),
    ]
    JOBS = [
        (0, _("Farmer")),
        (1, _("Craftsman")),
        (2, _("Artist")),
        (3, _("Manager")),
        (4, _("Driver")),
        (5, _("Chief Executive Officer")),
        (6, _("Clergyman")),
        (7, _("Independent retailer")),
        (8, _("Foreman, supervisor")),
        (9, _("Managing director")),
        (10, _("Employee")),
        (11, _("Student")),
        (12, _("Civil servant")),
        (13, _("Engineer")),
        (14, _("Primary schoolteacher")),
        (15, _("Labourer")),
        (16, _("Policeman or Soldier")),
        (17, _("Teacher")),
        (18, _("Self-employed profession")),
        (19, _("Pensioner")),
        (20, _("Sportsman")),
        (21, _("Technician")),
        (22, _("Undisclosed")),
        (23, _("Unemployed")),
        (24, _("Other")),
    ]
    PERSONALITIES = [
        (0, _("Adventurous")),
        (1, _("Calm")),
        (2, _("Considerate")),
        (3, _("Demanding")),
        (4, _("Funny")),
        (5, _("Generous")),
        (6, _("Proud")),
        (7, _("Reliable")),
        (8, _("Reserved")),
        (9, _("Sensitive")),
        (10, _("Shy")),
        (11, _("Sociable")),
        (12, _("Spontaneous")),
        (13, _("Other")),
    ]
    HOBBIES = [
        (0, _("Animals - Zoo - Nature")),
        (1, _("Antiques Fairs - Car boot sales")),
        (2, _("Art - Painting - Drawing")),
        (3, _("Cars - Motorbikes - Boats")),
        (4, _("Charity work")),
        (5, _("Cinema - Theatre")),
        (6, _("DIY - Gardening")),
        (7, _("Decoration")),
        (8, _("Events – Opera - Concerts")),
        (9, _("Exhibitions - Museums - Castles")),
        (10, _("Fairs")),
        (11, _("Games (cards/videos/roles)")),
        (12, _("Gastronomy - Oenology")),
        (13, _("History - Archaeology")),
        (14, _("Hunting - Fishing")),
        (15, _("IT - Web - Sciences")),
        (16, _("Philosophy - Sociology")),
        (17, _("Photography - Video")),
        (18, _("Poetry - Literature")),
        (19, _("Politics")),
        (20, _("Pool - Bowling")),
        (21, _("Restaurants - Picnics")),
        (22, _("Sea - Beach - Mountains - Skiing")),
        (23, _("Shopping")),
        (24, _("Song - Dance - Music")),
        (25, _("Sport")),
        (26, _("Television - Radio - Newspapers")),
        (27, _("Walking - Parks - Trade fairs")),
        (28, _("Weekends away")),
        (29, _("Writing - Reading")),
        (30, _("Other")),
    ]
    LICENSES = [
        (0, _("Boat")),
        (1, _("Car")),
        (2, _("HGV")),
        (3, _("Helicopter")),
        (4, _("Plane")),
        (5, _("Motorbike")),
        (6, _("Other")),
    ]

    LANGUAGES = [
        (0, _("English")),
        (1, _("Spanish")),
        (2, _("French")),
        (3, _("German")),
        (4, _("Italian")),
        (5, _("Portuguese")),
        (6, _("Russian")),
        (7, _("Polish")),
        (8, _("Japanese")),
        (9, _("Mandarin (Chinese)")),
        (10, _("Arab")),
        (11, _("Turkish")),
        (12, _("Bengali")),
        (13, _("No")),
        (14, _("Lahnda")),
        (15, _("Javanais")),
        (16, _("Vietnamese")),
        (17, _("Telugu")),
        (18, _("Korean")),
        (19, _("Urdu")),
        (20, _("Tamil")),
        (21, _("Marathi")),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    email = models.EmailField(_("email address"), unique=True, null=True)

    birthdate = models.DateField(_("date of birth"))
    covid = models.BooleanField(_("COVID-19 vaccine"), blank=True, null=True)
    help_ukranian = models.BooleanField(_("Help Ukranian"), default=False, null=True)
    handicap = models.BooleanField(_("I have a handicap"), default=False, null=True)
    sex = models.IntegerField(_("sex"), choices=SEX_CHOICES)

    place = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="place",
        verbose_name=_("place of living"),
    )

    birthplace = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("birthplace"),
    )
    nationality = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_("nationality"),
    )

    mothertongue = MultiSelectField(
        _("Mother Tongues"), choices=LANGUAGES, blank=True, null=True
    )
    languages = MultiSelectField(
        _("Spoken Languages"), choices=LANGUAGES, blank=True, null=True
    )

    level = models.IntegerField(
        _("education level"), choices=LEVELS, blank=True, null=True
    )
    subjects = MultiSelectField(
        _("study subjects"), choices=SUBJECTS, blank=True, null=True
    )
    sector = models.IntegerField(
        _("activity sector"), choices=SECTORS, blank=True, null=True
    )
    job = models.IntegerField(_("job"), choices=JOBS, blank=True, null=True)
    current = models.IntegerField(
        _("current employer"), choices=COMPANIES, blank=True, null=True
    )
    previous = models.IntegerField(
        _("previous employer"), choices=COMPANIES, blank=True, null=True
    )

    children = models.IntegerField(_("number of children"), blank=True, null=True)
    personalities = MultiSelectField(
        _("personalities"), choices=PERSONALITIES, blank=True, null=True
    )
    smoker = models.BooleanField(_("smoker"), blank=True, null=True)
    hobbies = MultiSelectField(_("hobbies"), choices=HOBBIES, blank=True, null=True)
    licenses = MultiSelectField(_("licenses"), choices=LICENSES, blank=True, null=True)
    how = models.IntegerField(
        _("how do you know CoGoFly?"), choices=HOW_CHOICES, blank=True, null=True
    )
    about = models.TextField(_("about you"), blank=True, null=True)

    picture = models.ImageField(
        _("profile picture"), upload_to=get_random_path, blank=True
    )
    cover = models.ImageField(_("cover picture"), upload_to=get_random_path, blank=True)

    album = GenericRelation("Picture")
    reactions = GenericRelation("Activity", related_query_name="profile")
    is_completed = models.BooleanField(_("is completed"), default=False)

    @property
    def age(self):
        today = datetime.date.today()
        return (
            today.year
            - self.birthdate.year
            - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        )

    @property
    def zodiac(self):
        bd = self.birthdate
        return ZODIAC_NAMES[ZODIAC_SIGNS[bisect(ZODIAC_SIGNS, (bd.month, bd.day))][2]][
            1
        ]

    @property
    def picture_url(self):
        return self.picture.url if self.picture else static("img/default-profile.png")

    @property
    def cover_url(self):
        return self.cover.url if self.cover else static("img/default-cover.jpg")

    IGNORE_FIELDS = ["id", "user", "birthdate", "sex", "place", "privacy"]

    @property
    def completion(self):
        important_fields = [
            field
            for field in self._meta.get_fields()
            if field.name not in self.IGNORE_FIELDS
        ]
        missing_fields = [
            field.verbose_name
            for field in important_fields
            if not getattr(self, field.name)
        ]
        completion = round(
            (len(important_fields) - len(missing_fields)) / len(important_fields) * 100
        )
        if completion == 100:
            Profile.objects.filter(user=self.user).update(is_complete=True)
            return dict(value=completion, missing_fields=missing_fields)

        return dict(value=completion, missing_fields=missing_fields)

    def get_absolute_url(self):
        return self.user.get_absolute_url()

    def __str__(self):
        return self.user.email


class Privacy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="privacy")

    class Levels(models.IntegerChoices):
        NOBODY = 0, _("Nobody")
        FRIENDS = 1, _("Friends only")
        EVERYBODY = 2, _("Everybody")

    birthplace = models.IntegerField(_("birthplace"), choices=Levels.choices, default=0)
    nationality = models.IntegerField(
        _("nationality"), choices=Levels.choices, default=0
    )

    mothertongue = models.IntegerField(
        _("mothertongue"), choices=Levels.choices, default=0
    )
    languages = models.IntegerField(_("languages"), choices=Levels.choices, default=0)

    zodiac = models.IntegerField(_("star sign"), choices=Levels.choices, default=0)

    level = models.IntegerField(_("education level"), choices=Levels.choices, default=0)
    subjects = models.IntegerField(
        _("study subjects"), choices=Levels.choices, default=0
    )
    sector = models.IntegerField(
        _("activity sector"), choices=Levels.choices, default=0
    )
    job = models.IntegerField(_("job"), choices=Levels.choices, default=0)
    current = models.IntegerField(
        _("current employer"), choices=Levels.choices, default=0
    )
    previous = models.IntegerField(
        _("previous employer"), choices=Levels.choices, default=0
    )

    children = models.IntegerField(
        _("number of children"), choices=Levels.choices, default=0
    )
    personalities = models.IntegerField(
        _("personalities"), choices=Levels.choices, default=0
    )
    hobbies = models.IntegerField(_("hobbies"), choices=Levels.choices, default=0)
    licenses = models.IntegerField(_("licenses"), choices=Levels.choices, default=0)
    handicap = models.IntegerField(_("handicap"), choices=Levels.choices, default=0)
    help_hukranian = models.IntegerField(
        _("help hukranian"), choices=Levels.choices, default=0
    )
    smoker = models.IntegerField(_("smoker"), choices=Levels.choices, default=0)
    about = models.IntegerField(_("about you"), choices=Levels.choices, default=0)
    album = models.IntegerField(_("album"), choices=Levels.choices, default=0)


class ContactRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    profile = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requests")
    message = models.CharField(max_length=200, blank=True)

    type = "contact"

    def accept(self):
        self.profile.contacts.add(self.user)
        self.delete()

    def decline(self):
        self.delete()


class Activity(models.Model):
    class Types(models.IntegerChoices):
        FAVORITE = 0
        LIKE = 1

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity")
    activity = models.IntegerField(choices=Types.choices)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()


class Picture(models.Model):
    picture = models.ImageField(upload_to=get_random_path)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()


class TripQueryset(models.QuerySet):
    def annotate_for(self, user):
        return self.annotate(
            Count("members"),
            is_favorite=Exists(
                user.activity.filter(
                    trip__id=OuterRef("pk"), activity=Activity.Types.FAVORITE
                )
            ),
            is_liked=Exists(
                user.activity.filter(
                    trip__id=OuterRef("pk"), activity=Activity.Types.LIKE
                )
            ),
            is_requested=Exists(
                TripRequest.objects.filter(trip__id=OuterRef("pk"), user=user)
            ),
        )

    def future(self):
        return self.filter(start__gte=datetime.date.today()).order_by("start")

    def past(self):
        return self.filter(start__lt=datetime.date.today()).order_by("-end")

    def last_added(self):
        return self.order_by("-created")

    def cotravels(self):
        return self.annotate(count=Count("members")).filter(count__gte=2)

    def next(self):
        return self.future().earliest("start")

    def previous(self):
        return self.past().latest("end")


class Trip(models.Model):
    destination = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="trips", null=True, blank=True
    )
    destination_country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="destination_country",
        null=True,
        blank=True,
    )
    destination_region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="destination_country",
        null=True,
        blank=True,
    )
    start = models.DateField(_("Departure date"), null=True, blank=True)
    end = models.DateField(_("Return date"), null=True, blank=True)
    departure = models.ForeignKey(
        City, on_delete=models.CASCADE, blank=True, null=True, related_name="+"
    )
    comment = models.TextField(_("Comment"), blank=True, null=True)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="own_trips", null=True, blank=True
    )
    members = models.ManyToManyField(User, related_name="trips", blank=True)

    reactions = GenericRelation("Activity", related_query_name="trip")
    pictures = GenericRelation("Picture")
    targeted_notifications = GenericRelation("Notification")

    created = models.DateTimeField(auto_now_add=True)

    objects = TripQueryset.as_manager()

    class Meta:
        ordering = ["start", "end"]

    """def __str__(self):
        return str(self.destination)"""

    def __str__(self):
        if self.destination != None:
            return str(self.destination)
        elif self.destination_region != None:
            return str(self.destination_region)
        else:
            return str(self.destination_country)

    def get_absolute_url(self):
        return reverse("trip", kwargs={"pk": self.id})

    def add(self, user):
        self.members.add(user)
        self.conversation.users.add(user)

    def remove(self, user):
        self.members.remove(user)
        self.conversation.users.remove(user)


class TripRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="requests")
    message = models.CharField(max_length=200, blank=True)
    confirmations = models.ManyToManyField(User, related_name="+")

    def accept(self, user):
        self.confirmations.add(user)
        if (
            self.trip.members.count()
            == self.trip.members.filter(id__in=self.confirmations.all()).count()
        ):
            self.trip.add(self.user)
            self.delete()
            return True

    def decline(self):
        self.delete()

    @property
    def accepted(self):
        return self.trip.members.filter(id__in=self.confirmations.all()).count()


class Conversation(models.Model):
    users = models.ManyToManyField(
        User, through="ConversationMembership", related_name="conversations"
    )
    trip = models.OneToOneField(
        "Trip", on_delete=models.CASCADE, null=True, related_name="conversation"
    )


class ConversationMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="membership"
    )
    last_seen = models.DateTimeField(auto_now=True)

    def unread(self, user):
        return self.conversation.filter(
            messages_created__gt=F("membership__last_seen")
        ).count()


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    created = models.DateTimeField(auto_now_add=True)
    text = models.CharField(max_length=200, blank=False)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.text


class Search(models.Model):
    class Meta:
        ordering = ["-created"]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="searches")
    created = models.DateTimeField(auto_now_add=True)

    departure = models.ForeignKey(
        City,
        verbose_name=_("departure city"),
        related_name="+",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    destination = models.ForeignKey(
        City,
        verbose_name=_("destination"),
        related_name="+",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    country = models.ForeignKey(
        Country,
        verbose_name=_("country"),
        related_name="+",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    start = models.DateField(_("date of departure"), blank=True, null=True)
    end = models.DateField(_("return date"), blank=True, null=True)

    language = MultiSelectField(
        _("language"), choices=Profile.LANGUAGES, blank=True, null=True
    )
    minage = models.IntegerField(_("minimum age"), blank=True, null=True)
    maxage = models.IntegerField(_("maximum age"), blank=True, null=True)
    covid = models.BooleanField(_("COVID-19 vaccine"), default=False)
    help_ukranian = models.BooleanField(_("Help ukranian"), default=False)
    handicap = models.BooleanField(_("handicap"), default=False)
    sex = models.IntegerField(
        _("Sex"), choices=Profile.SEX_CHOICES, blank=True, null=True
    )

    level = models.IntegerField(
        _("education level"), choices=Profile.LEVELS, blank=True, null=True
    )
    subjects = MultiSelectField(
        _("study subjects"), choices=Profile.SUBJECTS, blank=True, null=True
    )
    sector = models.IntegerField(
        _("activity sector"), choices=Profile.SECTORS, blank=True, null=True
    )
    job = models.IntegerField(_("job"), choices=Profile.JOBS, blank=True, null=True)
    current = models.CharField(
        _("current employer"), choices=COMPANIES, blank=True, max_length=40
    )
    previous = models.CharField(
        _("previous employer"), choices=COMPANIES, blank=True, max_length=40
    )

    children = models.PositiveIntegerField(
        _("number of children"), blank=True, null=True
    )
    zodiac = models.IntegerField(
        _("star sign"), choices=ZODIAC_NAMES, blank=True, null=True
    )
    personalities = MultiSelectField(
        _("personalities"), choices=Profile.PERSONALITIES, blank=True, null=True
    )
    nonsmoker = models.BooleanField(_("non-smokers only"), default=False)
    hobbies = MultiSelectField(
        _("hobbies"), choices=Profile.HOBBIES, blank=True, null=True
    )
    licenses = MultiSelectField(
        _("licenses"), choices=Profile.LICENSES, blank=True, null=True
    )

    @property
    def criteria_count(self):
        fields = self._meta.get_fields()
        return len(
            [
                field
                for field in fields
                if field.name not in ["destination", "start", "end"]
                and getattr(self, field.name)
            ]
        )

    @property
    def get_absolute_url(self):
        from cogofly.forms import SearchForm

        form = SearchForm(instance=self)
        # print(form.initial)
        values = []
        for field, value in form.initial.items():
            if value not in ["", None, []]:
                if isinstance(value, list):
                    values.extend((field, str(val)) for val in value)
                else:
                    values.append((field, str(value)))
        return (
            reverse("search")
            + "?"
            + "&".join(f"{field}={value}" for field, value in values)
        )


class PostQueryset(models.QuerySet):
    def annotate_for(self, user):
        return self.annotate(
            is_liked=Exists(
                user.activity.filter(
                    post__id=OuterRef("pk"), activity=Activity.Types.LIKE
                )
            ),
            nb_likes=Count(
                "reactions",
                filter=Q(reactions__activity=Activity.Types.LIKE),
                distinct=True,
            ),
            nb_comments=Count("comments", distinct=True),
        )


class Post(models.Model):
    class Meta:
        ordering = ["-published"]

    published = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    text = models.TextField(_("What's on your mind ?"), blank=True)

    pictures = GenericRelation("Picture")
    reactions = GenericRelation("Activity", related_query_name="post")
    targeted_notifications = GenericRelation("Notification")

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    shared_object = GenericForeignKey()

    notifications = GenericRelation("Notification")

    objects = PostQueryset.as_manager()

    def get_absolute_url(self):
        return reverse("post", kwargs={"pk": self.id})

    def __str__(self):
        return self.text


class CommentQueryset(models.QuerySet):
    def annotate_for(self, user):
        return self.annotate(
            is_liked=Exists(
                user.activity.filter(
                    comment__id=OuterRef("pk"), activity=Activity.Types.LIKE
                )
            ),
            nb_likes=Count(
                "reactions",
                filter=Q(reactions__activity=Activity.Types.LIKE),
                distinct=True,
            ),
        )


class Comment(models.Model):
    class Meta:
        ordering = ["-published"]

    published = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()

    reactions = GenericRelation("Activity", related_query_name="comment")
    targeted_notifications = GenericRelation("Notification")

    objects = CommentQueryset.as_manager()

    def __str__(self):
        return self.text

    def get_absolute_url(self):
        return reverse("post", kwargs={"pk": self.post.pk})


class Testimony(models.Model):
    class Meta:
        verbose_name_plural = "Testimonies"
        ordering = ["-created"]

    created = models.DateField(auto_now_add=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="testimony"
    )
    accepted = models.BooleanField(default=False)
    text = models.TextField()

    def __str__(self):
        return self.text


class Remark(models.Model):
    class Meta:
        ordering = ["-created"]

    created = models.DateField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text


class Notification(models.Model):
    class Meta:
        ordering = ["-updated"]

    class Types(models.IntegerChoices):
        FAVORITE = Activity.Types.FAVORITE, ngettext_lazy(
            "%(name)s has favorited your %(object)s",
            "%(name)s and %(value)d other people have favorited your %(object)s",
            "count",
        )
        LIKE = Activity.Types.LIKE, ngettext_lazy(
            "%(name)s has liked your %(object)s",
            "%(name)s and %(value)d other people have liked your %(object)s",
            "count",
        )

        COMMENT_OWN_POST = 2, ngettext_lazy(
            "%(name)s has commented your post",
            "%(name)s and %(value)d other people have commented your post",
            "count",
        )
        COMMENT_SAME_POST = 3, ngettext_lazy(
            "%(name)s has also commented this post",
            "%(name)s and %(value)d other people have also commented this post",
            "count",
        )

        ADD_TRIP = 4, _("%(name)s has added a trip")
        JOIN_SAME_TRIP = 5, _("%(name)s has joined your trip")
        JOIN_ANY_TRIP = 6, _("%(name)s has joined a trip")
        TRIP_REQUEST_ACCEPTED = 7, _("Your trip request has been accepted")

        NEW_FRIEND = 8, _("You are now friend with %(name)s")

    updated = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.IntegerField(choices=Types.choices)
    read = models.BooleanField(default=False)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey()

    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text

    def get_absolute_url(self):
        return reverse("notification", kwargs={"pk": self.pk})


from . import notifications
