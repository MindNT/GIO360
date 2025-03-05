from flask import Flask, request, jsonify
import requests
import json
import math
import time
import os
from typing import Dict, List
from datetime import datetime
from dotenv import load_dotenv
from collections import Counter

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

class RestaurantFinder:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Falta la clave API de Google. Defínela en el archivo .env")
        
        self.base_url = "https://maps.googleapis.com/maps/api/place"

    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        url = f"{self.base_url}/{endpoint}/json"
        params['key'] = self.api_key
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371000  # Radio de la Tierra en metros
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi, delta_lambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)

        a = (math.sin(delta_phi / 2) ** 2) + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def search_restaurants(self, address: str) -> Dict:
        try:
            place_params = {'input': address, 'inputtype': 'textquery', 'fields': 'place_id,geometry'}
            place_response = self._make_request('findplacefromtext', place_params)

            if not place_response.get('candidates'):
                return {"status": "error", "message": "No se encontró la ubicación especificada"}

            place = place_response['candidates'][0]
            origin_lat, origin_lng = place['geometry']['location']['lat'], place['geometry']['location']['lng']

            all_restaurants, next_page_token = [], None
            nearby_params = {'location': f"{origin_lat},{origin_lng}", 'type': 'restaurant', 'rankby': 'distance'}

            while True:
                if next_page_token:
                    nearby_params['pagetoken'] = next_page_token

                response = self._make_request('nearbysearch', nearby_params)
                restaurants = response.get('results', [])

                for restaurant in restaurants:
                    lat, lng = restaurant['geometry']['location']['lat'], restaurant['geometry']['location']['lng']
                    distance = self._calculate_distance(origin_lat, origin_lng, lat, lng)
                    if distance <= 10000:
                        details_params = {
                            'place_id': restaurant['place_id'],
                            'fields': 'name,rating,formatted_address,reviews,opening_hours,website,price_level,types,user_ratings_total,current_opening_hours,serves_beer,serves_breakfast,serves_lunch,serves_dinner'
                        }
                        details = self._make_request('details', details_params).get('result', {})

                        # Reseñas
                        reviews = details.get('reviews', [])
                        total_reviews = len(reviews)
                        good_reviews = [r['text'] for r in reviews if r.get('rating', 0) >= 4][:3]
                        bad_reviews = [r['text'] for r in reviews if r.get('rating', 0) <= 2][:3]
                        good_review_count = sum(1 for r in reviews if r.get('rating', 0) >= 4)
                        bad_review_count = sum(1 for r in reviews if r.get('rating', 0) <= 2)

                        # Palabras clave en reseñas
                        all_review_texts = " ".join(r.get('text', '') for r in reviews).lower().split()
                        keyword_counts = Counter(all_review_texts)
                        common_keywords = [word for word, count in keyword_counts.most_common(10) if len(word) > 3]

                        # Categoría del restaurante
                        category = details.get('types', [None])[0]

                        # Tiempo de espera estimado (si está disponible)
                        estimated_wait_time = details.get('current_opening_hours', {}).get('wait_times', None)

                        # Servicios disponibles
                        services = {
                            "Dine-in": details.get('serves_dinner', False),
                            "Takeaway": details.get('serves_lunch', False),
                            "Delivery": details.get('serves_breakfast', False)
                        }

                        # Rango de precios
                        price_range = details.get('price_level', "Desconocido")

                        # Promociones o descuentos (si se mencionan en reseñas)
                        promotions = [r['text'] for r in reviews if "descuento" in r.get('text', '').lower() or "promoción" in r.get('text', '').lower()]

                        restaurant_data = {
                            "name": details.get('name'),
                            "address": details.get('formatted_address'),
                            "coordinates": {"lat": lat, "lng": lng},
                            "distance_meters": round(distance),
                            "rating": details.get('rating'),
                            "total_reviews": total_reviews,
                            "positive_reviews": {
                                "count": good_review_count,
                                "reviews": good_reviews
                            },
                            "negative_reviews": {
                                "count": bad_review_count,
                                "reviews": bad_reviews
                            },
                            "common_keywords": common_keywords,
                            "category": category,
                            "estimated_wait_time": estimated_wait_time,
                            "services_available": services,
                            "price_range": price_range,
                            "promotions_or_discounts": promotions,
                            "opening_hours": details.get('opening_hours', {}).get('weekday_text', []),
                            "website": details.get('website')
                        }
                        all_restaurants.append(restaurant_data)

                next_page_token = response.get('next_page_token')
                if not next_page_token or len(all_restaurants) >= 6:
                    break
                time.sleep(2)

            all_restaurants.sort(key=lambda x: x['distance_meters'])
            result = {"meta": {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, "restaurants": all_restaurants}

            return result

        except Exception as e:
            return {"status": "error", "message": str(e)}

@app.route('/buscar_restaurantes', methods=['GET'])
def buscar_restaurantes():
    direccion = request.args.get('direccion')
    if not direccion:
        return jsonify({"status": "error", "message": "Debe proporcionar una dirección"}), 400

    finder = RestaurantFinder()
    resultado = finder.search_restaurants(direccion)
    
    return app.response_class(
        response=json.dumps(resultado, ensure_ascii=False, indent=2),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(debug=True)
