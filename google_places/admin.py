from django.contrib import admin

from .models import (
    PlaceType, Place, AddressComponentType, AddressComponent, OpenPeriod,
    Review, ReviewAspect, Photo
)


@admin.register(PlaceType)
class PlaceTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    pass


@admin.register(AddressComponentType)
class AddressComponentTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(AddressComponent)
class AddressComponentAdmin(admin.ModelAdmin):
    pass


@admin.register(OpenPeriod)
class OpenPeriodAdmin(admin.ModelAdmin):
    pass


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    pass


@admin.register(ReviewAspect)
class ReviewAspectAdmin(admin.ModelAdmin):
    pass


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    pass
