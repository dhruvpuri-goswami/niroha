from django.urls import path
from .views import hello_world, upload_files, upload_success, limit, plantID

urlpatterns = [
    path('hello/', hello_world, name='hello'),
    path('rohantheboss/', upload_files, name='upload_files'),
    path('rohantheboss/success/', upload_success, name='upload_success'),
    path('limit/', limit, name='limit'),
    path('plantID/<str:plant_id>/', plantID, name='plantID'),
]
