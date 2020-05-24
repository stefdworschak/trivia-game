from django.shortcuts import render

# Create your views here.
def cah_party(request, party_id):
    return render(request, 'cah_party.html')