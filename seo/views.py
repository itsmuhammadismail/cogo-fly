from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from .forms import SearchForm



@login_required
@permission_required('is_superuser')
def interface(request):
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            ctx={
                'form': form,
            }

            return render(request, "seo/interface.html", ctx)

    return render(request, 'seo/interface.html')
