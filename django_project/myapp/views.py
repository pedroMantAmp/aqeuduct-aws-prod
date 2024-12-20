from django.http import HttpResponse

def home(_request):
    return HttpResponse("Hello, Django!")