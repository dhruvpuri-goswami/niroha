from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from firebase_admin import db, storage
import os
from datetime import timedelta


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

# New Endpoint: /limit
def limit(request):
    # Get the limit parameter from the query string
    limit = int(request.GET.get('limit', 10))  # Default to 10 if not provided
    
    # Fetch all plants
    ref = db.reference('plants')
    plants = ref.get()

    # Limit the number of plants returned
    limited_plants = dict(list(plants.items())[:limit])

    return JsonResponse(limited_plants)

# New Endpoint: /plantID/<str:plant_id>
def plantID(request, plant_id):
    # Fetch specific plant details from Firebase Realtime Database
    ref = db.reference(f'plants/{plant_id}')
    plant_details = ref.get()

    if not plant_details:
        return HttpResponseBadRequest(f'Plant ID {plant_id} not found.')

    return JsonResponse(plant_details)