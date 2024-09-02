from django.urls import path
from .views import hello_world, upload_files, upload_success

urlpatterns = [
    path('hello/', hello_world, name='hello'),
    path('rohantheboss/', upload_files, name='upload_files'),
    path('rohantheboss/success/', upload_success, name='upload_success'),
]
