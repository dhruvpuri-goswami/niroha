from django.urls import path
from .views import hello_world, upload_files, upload_success, limit, plant_details

urlpatterns = [
    path('hello/', hello_world, name='hello'),
    path('rohantheboss/', upload_files, name='upload_files'),
    path('rohantheboss/success/', upload_success, name='upload_success'),
    path('limit/<int:limit>/', limit, name='limit'),
    path('<str:plant_id>/', plant_details, name='plant_details'),
]
