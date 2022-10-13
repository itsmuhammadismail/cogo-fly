from django import forms


class SearchForm(forms.Form):
    search_query = forms.CharField(label="What do you wants to see?", max_length=100)

