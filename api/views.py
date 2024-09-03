from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import render, redirect
from firebase_admin import db, storage
import os
from datetime import timedelta
from urllib.parse import unquote
import re

def hello_world(request):
    return JsonResponse({'message': 'Hello'})

def upload_files(request):
    # Fetch plant data from Firebase Realtime Database
    ref = db.reference('plants')
    plants = ref.get()

    plant_choices = [(plant_id, plant_data.get('scientific_name', plant_id)) for plant_id, plant_data in plants.items()]

    if request.method == 'POST':
        plant_id = request.POST.get('plant_id')
        ai_images = request.FILES.getlist('ai_images')
        org_images = request.FILES.getlist('org_images')
        videos = request.FILES.getlist('videos')
        models = request.FILES.getlist('models')

        # Firebase Storage bucket
        bucket = storage.bucket()

        # Function to upload files to Firebase Storage and store their URLs in the database
        def upload_to_firebase(file_list, category):
            # Retrieve existing URLs from the database (if any)
            existing_urls_ref = db.reference(f'plants/{plant_id}/{category}')
            existing_urls = existing_urls_ref.get() or []

            file_urls = existing_urls.copy()  # Start with existing URLs

            for f in file_list:
                file_name = f.name
                blob = bucket.blob(f'{plant_id}/{category}/{file_name}')
                blob.upload_from_file(f)

                # Get the public URL
                file_url = blob.generate_signed_url(expiration=timedelta(days=3650))  # 10-year expiration
                file_urls.append(file_url)

            # Update the database with the new list of URLs
            existing_urls_ref.set(file_urls)

        # Upload files to corresponding categories
        if ai_images:
            upload_to_firebase(ai_images, 'ai_images')
        if org_images:
            upload_to_firebase(org_images, 'org_images')
        if videos:
            upload_to_firebase(videos, 'videos')
        if models:
            upload_to_firebase(models, 'models')

        return redirect('upload_success')
    else:
        context = {'plant_choices': plant_choices}
        return render(request, 'upload.html', context)

def upload_success(request):
    return render(request, 'success.html')

def find_first_number_with_text(size_str):
    # Find the first number and its following text
    match = re.search(r"(\d+\.?\d*)\s*([a-zA-Z]+)", size_str)
    unit = match.groups() if match else "NOT_AVAILABLE"
    return ' '.join(unit)

# New Endpoint: /limit/<int:limit>
def limit(request, limit):
    if limit <= 0:
        return HttpResponseBadRequest('Limit must be a positive integer.')

    # Fetch all plants
    ref = db.reference('plants')
    plants = ref.get()

    # Limit the number of plants returned
    limited_plants = dict(list(plants.items())[:limit])

    # Add the first number and its text to each plant's data
    for plant_id, plant_data in limited_plants.items():
        size_str = plant_data.get('description', {}).get('size', "")
        first_number_with_text = find_first_number_with_text(size_str)
        plant_data['size_unit'] = first_number_with_text

    return JsonResponse(limited_plants)

def create_simplified_description(plant):
    name = plant.get('common_names', [''])[0]
    scientific_name = plant.get('scientific_name', '')
    family = plant.get('family', '')
    native_region = plant.get('habitat_distribution', {}).get('native_region', '')
    appearance = plant.get('description', {}).get('appearance', '')
    size = plant.get('description', {}).get('size', '')
    climate = plant.get('habitat_distribution', {}).get('preferred_climate', '').replace(".", "").lower()
    soil = plant.get('habitat_distribution', {}).get('soil_requirements', '').replace(".", "").lower()
    sunlight = plant.get('habitat_distribution', {}).get('sunlight_needs', '').replace(".", "").lower()
    medicinal_properties = ', '.join(plant.get('medicinal_uses', {}).get('therapeutic_properties', []))
    ayurveda_uses = plant.get('medicinal_uses', {}).get('applications_in_ayush', {}).get('ayurveda', '')
    cultural_significance = plant.get('cultural_historical_significance', {}).get('historical_use', '')

    description = (
        f"{name} ({scientific_name}) is a plant native to {native_region} and belongs to the {family} family. "
        f"It is recognized by its {appearance}. It typically grows up to {size}. "
        f"This plant thrives in {climate}, preferring {soil} and {sunlight}. "
        f"Medically, it is known for its {medicinal_properties} properties. "
        f"In Ayurveda, it is commonly used {ayurveda_uses.lower().strip()}. "
        f"Culturally, {name.lower()} has been significant for {cultural_significance.lower().strip()}."
    )

    description = description.replace("..", ".").replace(". .", ". ").replace(" ,", ",").replace("  ", " ").strip()

    return description

# New Endpoint: /plantid/<str:plant_id>
def plant_details(request, plant_id):

    ref = db.reference(f'plants/{plant_id}')
    plant_details = ref.get()

    if not plant_details:
        return HttpResponseNotFound(f'Plant ID {plant_id} not found.')

    plant_desc = create_simplified_description(plant_details)

    plant_details['simplified_description'] = plant_desc

    return JsonResponse(plant_details)

# New Endpoint: /plant/<str:name>
def search_plant_by_name(request, plant_name):
    ref = db.reference('plants')
    plants = ref.get()

    search_query = unquote(plant_name).lower()

    print(search_query)

    for plant_id, plant_data in plants.items():
        scientific_name = plant_data.get('scientific_name', '').lower()
        common_names = [name.lower() for name in plant_data.get('common_names', [])]

        if search_query in scientific_name or search_query in common_names:
            return JsonResponse(plant_data)

    return HttpResponseNotFound(f'No plant found with the name "{plant_name}".')

# New Endpoint: /plant/therapeutic/<str:therapeutic>
def search_plant_by_therapeutic_property(request, therapeutic):
    ref = db.reference('plants')
    plants = ref.get()

    search_query = therapeutic.lower()

    matching_plants = []

    for plant_id, plant_data in plants.items():
        therapeutic_properties = [prop.lower() for prop in plant_data.get('medicinal_uses', {}).get('therapeutic_properties', [])]
        ayush_applications = plant_data.get('medicinal_uses', {}).get('applications_in_ayush', {})
        combined_text = ' '.join(therapeutic_properties + list(ayush_applications.values())).lower()

        if search_query in combined_text:
            matching_plants.append(plant_data)

    if not matching_plants:
        return HttpResponseNotFound(f'No plants found containing the term "{therapeutic}".')

    return JsonResponse(matching_plants, safe=False)

