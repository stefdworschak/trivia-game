from django.urls import path

from . import views

urlpatterns = [
    path('<str:party_id>/finish', views.finish_screen, name='finish_screen'),
    path('<str:party_id>/waiting', views.waiting_screen, name='waiting_screen'),
    path('<str:party_id>/party', views.cah_party, name='cah_party'),
    path('<str:party_id>/submission', views.submit_card, name='submission'),
    path('<str:party_id>/choose', views.choose_screen, name='choose_screen'),
    path('<str:party_id>/mark_revealed', views.mark_revealed, name='mark_revealed'),
    path('<str:party_id>/submit_winner', views.submit_winner, name='submit_winner'),
]