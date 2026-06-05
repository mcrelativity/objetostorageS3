from django.shortcuts import render
from django.core.files.storage import default_storage

def index(request):
    images = []
    try:
        directories, files = default_storage.listdir('')
        valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg')
        image_files = [f for f in files if f.lower().endswith(valid_extensions)]
        images = [default_storage.url(f) for f in image_files]
    except Exception as e:
        print(e)
    
    return render(request, 'gallery/index.html', {'images': images})