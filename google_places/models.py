from django.db import models
from django.conf import settings
from django.utils import timezone

from googleplaces import GooglePlaces

from decimal import Decimal
import hashlib
from datetime import datetime, time


google_places = GooglePlaces(settings.GOOGLE_PLACES_API_KEY)


class PlaceType(models.Model):
    """
    Represents a type of place or a feature of that place.

    @see https://developers.google.com/places/documentation/supported_types
    """
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name.title()


class PlaceManager(models.Manager):
    def get_or_create(self, **kwargs):
        if 'reference' in kwargs:
            kwargs.update(reference_sha1=Place.create_reference_sha1(
                kwargs.get('reference')))
            del kwargs['reference']
        return super().get_or_create(kwargs)

    def filter(self, reference=None, **kwargs):
        if 'reference' in kwargs:
            kwargs.update(
                reference_sha1=Place.create_reference_sha1(
                    kwargs.get('reference')
                )
            )
            del kwargs['reference']
        return super().filter(self, **kwargs)

    def exclude(self, **kwargs):
        if 'reference' in kwargs:
            kwargs.update(
                reference_sha1=Place.create_reference_sha1(
                    kwargs.get('reference')
                )
            )
            del kwargs['reference']
        return super().exclude(self, **kwargs)

    def reference(self, reference):
        return self.filter(
            reference_sha1=Place.create_reference_sha1(reference))


class Place(models.Model):
    """
    Represents a Google Place as retrieved using the Place Details service.

    @see https://developers.google.com/places/documentation/details#PlaceDetailsResults
    """
    STATUS_SYNC = 'sync'          # This place is currently being sync'd
    STATUS_ACTIVE = 'active'      # This place has been sync'd
    STATUS_INACTIVE = 'inactive'  # This place is considered 'inactive' by the local application
    STATUS_DELETED = 'deleted'    # This place has been or is considered deleted by the local application
    STATUS_CHOICES = (
        (STATUS_SYNC, 'Sync'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_DELETED, 'Deleted'),
    )

    name = models.CharField(max_length=255, help_text='The human-readable name for the place. For establishment results, this is usually the canonicalized business name.')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    place_types = models.ManyToManyField(PlaceType, help_text='Feature types describing the given place.', related_name='places')
    website = models.URLField(null=True, blank=True, help_text="The authoritative website for this Place, such as a business' homepage.")
    formatted_address = models.CharField(max_length=255, help_text='The human-readable address of this place - composed of one or more address components.')
    vicinity = models.CharField(max_length=255, help_text='A simplified address for the Place, including the street name, street number, and locality, but not the province/state, postal code, or country.')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="The places' geocoded latitude.")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, help_text="The places' geocoded longitude.")
    icon = models.URLField(null=True, blank=True, help_text='URL of a suggested icon which may be displayed to the user when indicating this result on a map.')
    formatted_phone_number = models.CharField(max_length=64, null=True, blank=True, help_text="The Place's phone number in its local format.")
    international_phone_number = models.CharField(max_length=255, null=True, blank=True, help_text="Phone number in international format.")
    rating = models.DecimalField(null=True, blank=True, max_digits=3, decimal_places=2, help_text="Place's rating, from 1.0 to 5.0, based on user reviews.")
    url = models.URLField(null=True, blank=True, help_text='The official Google Place Page URL of this establishment.')
    utc_offset = models.IntegerField(null=True, blank=True, help_text="The number of minutes this Place's current timezone is offset from UTC.")
    reference_sha1 = models.CharField(max_length=40, null=True, blank=True, unique=True, help_text='A sha1 of the reference - used for ensuring uniqueness of reference\'s.')
    reference = models.TextField(help_text='A token that can be used to query the Google Places Details service in future.')
    api_id = models.CharField(max_length=191, unique=True, help_text="Unique stable identifier denoting this place.")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    syncd = models.DateTimeField(auto_now_add=True, help_text="When this place was last sync'd with Google's Places API.")

    objects = PlaceManager

    def __str__(self):
        return self.formatted_address

    @staticmethod
    def create_reference_sha1(reference):
        return hashlib.sha1(reference.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        if self.reference is not None:
            self.reference_sha1 = Place.create_reference_sha1(self.reference)
        return super(Place, self).save(*args, **kwargs)

    def get_from_api(self):
        return google_places.get_place(self.reference)

    def refresh_from_api(self):
        """
        Refresh this place using the API.
        """
        self.populate_from_api(self.get_from_api())

    def populate_from_api(self, place, details=True):
        """
        Populate this object and associated objects with place details.

        @param place: A googleplaces.Place instance.
        """
        if self.pk:
            # We're populating an existing Place,
            # make sure folks know it's being updated...
            self.status = self.STATUS_SYNC
            self.save(update_fields=('status',))

        self.name = place.name
        self.api_id = place.id
        self.reference = place.reference
        self.latitude = Decimal(str(place.geo_location.get('lat')))
        self.longitude = Decimal(str(place.geo_location.get('lng')))

        if not details:
            self._query_instance = place._query_instance
            self.save()
            return

        # Ensure there are details
        if details:
            place.get_details()
            self.formatted_address = place.formatted_address
            self.website = place.website
            self.vicinity = place.vicinity
            self.icon = place.icon
            self.formatted_phone_number = place.details.get(
                'formatted_phone_number'
            )
            self.international_phone_number = place.details.get(
                'international_phone_number'
            )
            self.rating = Decimal(str(place.rating)) if place.rating else None
            self.url = place.url
            self.utc_offset = place.details.get('utc_offset')
            self.save()

        # Place Types
        self.place_types.clear()
        for place_type_name in place.types:
            place_type, created = PlaceType.objects.get_or_create(name=place_type_name)
            self.place_types.add(place_type)

        # Address Components
        self.address_components.all().delete()
        for _address_component in place.details.get('address_components', []):
            # {u'long_name': u'31', u'types': [u'street_number'], u'short_name': u'31'}
            address_component = self.address_components.create(long_name=_address_component.get('long_name'),
                                                               short_name=_address_component.get('short_name'))
            for address_component_name in _address_component.get('types'):
                address_component_type, created = AddressComponentType.objects.get_or_create(name=address_component_name)
                address_component.types.add(address_component_type)

        # Opening Periods
        self.opening_periods.all().delete()
        for period in place.details.get('opening_hours', {}).get('periods', []):
            # {u'close': {u'day': 1, u'time': u'1800'}, u'open': {u'day': 1, u'time': u'0800'}}
            # or in some cases (say.. Google Pty Ltd)
            # {u'open_now': True, u'periods': [{u'open': {u'day': 0, u'time': u'0000'}}]}
            if period.get('close', {}).get('time', False) and \
               period.get('close', {}).get('day', False) and \
               period.get('open', {}).get('time', False) and \
               period.get('open', {}).get('day', False):
                close_time = period.get('close', {}).get('time', None)
                close_time = time(int(close_time[:2]), int(close_time[-2:]))
                open_time = period.get('open', {}).get('time', None)
                open_time = time(int(open_time[:2]), int(open_time[-2:]))
                self.opening_periods.create(close_day=period.get('close', {}).get('day', None),
                                            close_time=close_time,
                                            open_day=period.get('open', {}).get('day', None),
                                            open_time=open_time)

        # Reviews
        self.reviews.all().delete()
        for _review in place.details.get('reviews', []):
            """
            {u'rating': 1,
             u'aspects': [{u'rating': 0, u'type': u'overall'}],
             u'text': u'Awesome service...',
             u'author_name': u'John Doe',
             u'author_url': u'https://plus.google.com/123456789123456789123456789',
             u'time': 1384123362}
            """
            review = self.reviews.create(rating=_review.get('rating'),
                                         text=_review.get('text'),
                                         author_name=_review.get('author_name'),
                                         author_url=_review.get('author_url'),
                                         reviewed=datetime.fromtimestamp(_review.get('time')))
            for _review_aspect in _review.get('aspects', []):
                review.aspects.create(aspect_type=_review_aspect['type'],
                                      rating=_review_aspect['rating'])

        self.photos.all().delete()
        for _review in place.details.get('photos', []):
            self.photos.create(
                width=_review.get('width'),
                height=_review.get('height'),
                reference=_review.get('photo_reference')
            )

        self.status = self.STATUS_ACTIVE
        self.syncd = timezone.now()
        self.save(update_fields=('status',))


class AddressComponentType(models.Model):
    """
    Indicates the type of the address component.
    """
    name = models.CharField(max_length=191, unique=True)

    def __str__(self):
        return self.name


class AddressComponent(models.Model):
    """
    Separate address components used to compose a given address.
    """
    place = models.ForeignKey(Place, related_name='address_components')
    types = models.ManyToManyField(
        AddressComponentType,
        related_name='address_components'
    )
    long_name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255)

    def __str__(self):
        return self.short_name


class OpenPeriod(models.Model):
    """
    Represents an open/close hour for a place.
    """
    DAYS_OF_WEEK = (
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    )
    place = models.ForeignKey(Place, related_name='opening_periods')
    open_day = models.SmallIntegerField(choices=DAYS_OF_WEEK)
    open_time = models.TimeField()
    close_day = models.SmallIntegerField(choices=DAYS_OF_WEEK)
    close_time = models.TimeField()

    def __str__(self):
        if self.open_day != self.close_day:
            return '{} {} to {} {}'.format(self.get_open_day_display(),
                                           self.open_time,
                                           self.get_close_day_display(),
                                           self.close_time)
        else:
            return '{} {} to {}'.format(self.get_open_day_display(),
                                        self.open_time,
                                        self.close_time)


class Review(models.Model):
    """
    Represents a review of a place.
    """
    place = models.ForeignKey(Place, related_name='reviews')
    author_name = models.CharField(max_length=255)
    author_url = models.CharField(max_length=255, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    text = models.TextField()
    reviewed = models.DateTimeField()

    def __str__(self):
        return '{} by {}'.format(self.rating, self.author_name)


class ReviewAspect(models.Model):
    """
    Rating of a single attribute of a review.

    The first object in the collection is considered the primary aspect.
    """
    ASPECT_TYPE_APPEAL = 'appeal'
    ASPECT_TYPE_ATMOSPHERE = 'atmosphere'
    ASPECT_TYPE_DECOR = 'decor'
    ASPECT_TYPE_FACILITIES = 'facilities'
    ASPECT_TYPE_FOOD = 'food'
    ASPECT_TYPE_OVERALL = 'overall'
    ASPECT_TYPE_QUALITY = 'quality'
    ASPECT_TYPE_SERVICE = 'service'
    ASPECT_TYPE_CHOICES = (
        (ASPECT_TYPE_APPEAL, 'Appeal'),
        (ASPECT_TYPE_ATMOSPHERE, 'Atmosphere'),
        (ASPECT_TYPE_DECOR, 'Decor'),
        (ASPECT_TYPE_FACILITIES, 'Facilities'),
        (ASPECT_TYPE_FOOD, 'Food'),
        (ASPECT_TYPE_OVERALL, 'Overall'),
        (ASPECT_TYPE_QUALITY, 'Quality'),
        (ASPECT_TYPE_SERVICE, 'Service'),
    )

    review = models.ForeignKey(Review, related_name='aspects')
    aspect_type = models.CharField(max_length=32, choices=ASPECT_TYPE_CHOICES)
    rating = models.SmallIntegerField(
        help_text="Author's rating for this particular aspect, from 0 to 3."
    )

    def __str__(self):
        return '{} for {}'.format(self.rating, self.get_aspect_type_display())


class Photo(models.Model):
    """
    Represents a photo of a place.
    """
    place = models.ForeignKey(Place, related_name='photos')
    width = models.IntegerField()
    height = models.IntegerField()
    reference = models.TextField(
        help_text='A token that can be used to query the Google Photos service.'
    )

    def __str__(self):
        return '{} x {} photo of {}'.format(
            self.width, self.height, self.place
        )

