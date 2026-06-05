from django.shortcuts import render

def index(request):
    # Simulando los enlaces que luego vendrán de tu bucket S3
    dummy_images = [
        "https://picsum.photos/id/1018/800/600",
        "https://picsum.photos/id/1015/800/600",
        "https://picsum.photos/id/1019/800/600",
        "https://picsum.photos/id/1016/800/600",
        "https://picsum.photos/id/1020/800/600",
        "https://picsum.photos/id/1021/800/600",
    ]
    
    return render(request, 'gallery/index.html', {'images': dummy_images})