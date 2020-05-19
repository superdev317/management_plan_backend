from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from .models import google_places, Place
from .serializers import PlaceAddressSerializer

import pickle


class PlaceAddressAutocompliteListView(views.APIView):
    """
    Endpoint for autocomplite addresses from google place
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        """
        Get lists of addresses from google place
        """

        q = request.GET.get('q')

        if not q:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        addresses = []

        results = cache.get('google_places_autocomplete::{}'.format(q))
        if not results:
            results = google_places.autocomplete(input=q)
            pickled_object = pickle.dumps(results)
            cache.set(
                'google_places_autocomplete::{}'.format(q), pickled_object
            )
            cache.expire(
                'google_places_autocomplete::{}'.format(q), 60 * 60 * 24
            )
        else:
            results = pickle.loads(results)

        for prediction in results.predictions:
            prediction.get_details()
            addresses.append(prediction)
            # addresses.append({'address': p})
        return Response(PlaceAddressSerializer(addresses, many=True).data)
