from django.urls import path
from .views import hello_world, upload_files, upload_success, limit, plant_details, search_plant_by_name, search_plant_by_therapeutic_property

urlpatterns = [
    path('hello/', hello_world, name='hello'),
    path('rohantheboss/', upload_files, name='upload_files'),
    path('rohantheboss/success/', upload_success, name='upload_success'),
    path('limit/<int:limit>/', limit, name='limit'),
    path('plantid/<str:plant_id>/', plant_details, name='plant_details'),
    path('plant/<str:plant_name>/', search_plant_by_name, name='search_plant_by_name'),
    path('plant/therapeutic/<str:therapeutic>/', search_plant_by_therapeutic_property, name='search_plant_by_therapeutic_property'),
]
