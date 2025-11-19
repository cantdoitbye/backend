from django.conf import settings
from django.http import JsonResponse
from django.views import View

import requests


class GoogleLocationSearchView(View):
    places_endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    place_details_endpoint = "https://maps.googleapis.com/maps/api/place/details/json"

    def get(self, request):
        query = request.GET.get("query")
        if not query:
            return JsonResponse(
                {"error": "Missing required query parameter `query`."},
                status=400,
            )

        api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", None)
        if not api_key:
            return JsonResponse(
                {"error": "Google Maps API key not configured."},
                status=500,
            )

        params = {"key": api_key, "query": query}
        for optional in ("language", "region", "type"):
            value = request.GET.get(optional)
            if value:
                params[optional] = value

        try:
            response = requests.get(
                self.places_endpoint,
                params=params,
                timeout=5,
            )
        except requests.RequestException as exc:
            return JsonResponse(
                {
                    "error": "Failed to reach Google Maps API.",
                    "details": str(exc),
                },
                status=502,
            )

        try:
            payload = response.json()
        except ValueError:
            return JsonResponse(
                {
                    "error": "Google Maps API did not return valid JSON.",
                },
                status=502,
            )

        if response.status_code >= 400:
            return JsonResponse(
                {
                    "error": "Google Maps API error.",
                    "status": response.status_code,
                    "payload": payload,
                },
                status=502,
            )

        # Format the response with relevant location information
        formatted_results = self._format_locations(payload.get("results", []), api_key)
        
        return JsonResponse({
            "status": payload.get("status"),
            "count": len(formatted_results),
            "results": formatted_results,
        })
    
    def _format_locations(self, results, api_key):
        """Extract and format important location information."""
        formatted = []
        
        for place in results:
            place_id = place.get("place_id")
            
            # Fetch detailed information from Place Details API
            address_components = []
            if place_id:
                details = self._get_place_details(place_id, api_key)
                if details:
                    address_components = details.get("address_components", [])
            
            # Try multiple strategies to extract location info
            city = self._extract_component(address_components, ["locality"])
            if not city:
                city = self._extract_component(address_components, ["sublocality", "sublocality_level_1"])
            
            state = self._extract_component(address_components, ["administrative_area_level_1"])
            county = self._extract_component(address_components, ["administrative_area_level_2"])
            country = self._extract_component(address_components, ["country"])
            postal_code = self._extract_component(address_components, ["postal_code"])
            
            # Fallback: Parse from formatted_address if components not available
            formatted_address = place.get("formatted_address", "")
            if not address_components and formatted_address:
                address_parts = [part.strip() for part in formatted_address.split(",")]
                if len(address_parts) >= 2:
                    city = address_parts[0] if not city else city
                    if len(address_parts) >= 3:
                        state_postal = address_parts[-2].strip()
                        # Try to extract state and postal code from "State 123456" format
                        parts = state_postal.split()
                        if parts:
                            state = " ".join([p for p in parts if not p.isdigit()]) if not state else state
                            for p in parts:
                                if p.isdigit():
                                    postal_code = p if not postal_code else postal_code
                    country = address_parts[-1] if not country else country
            
            # Get geometry/location data
            geometry = place.get("geometry", {})
            location = geometry.get("location", {})
            
            formatted_place = {
                "id": place_id,
                "name": place.get("name"),
                "formatted_address": formatted_address,
                "address": {
                    "city": city,
                    "state": state,
                    "county": county,
                    "country": country,
                    "postal_code": postal_code,
                },
                "location": {
                    "latitude": location.get("lat"),
                    "longitude": location.get("lng"),
                },
                "types": place.get("types", []),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("user_ratings_total"),
                "business_status": place.get("business_status"),
            }
            
            formatted.append(formatted_place)
        
        return formatted
    
    def _get_place_details(self, place_id, api_key):
        """Fetch place details to get address components."""
        try:
            response = requests.get(
                self.place_details_endpoint,
                params={
                    "place_id": place_id,
                    "key": api_key,
                    "fields": "address_components"
                },
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("result", {})
        except requests.RequestException:
            # If details fetch fails, continue without it
            pass
        return None
    
    def _extract_component(self, components, types):
        """Extract address component by type(s)."""
        for component in components:
            for comp_type in types:
                if comp_type in component.get("types", []):
                    return component.get("long_name")
        return None
