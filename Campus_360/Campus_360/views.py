from django.shortcuts import redirect, render
from django.http import HttpResponse

def home(request):
    # return HttpResponse("<h2> This is home page.</h2>")
    return render(request, 'home.html')