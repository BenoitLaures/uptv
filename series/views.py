"""Views for series app."""
from django.urls import reverse
from django.views.generic import FormView, View
from series.forms import SearchSeriesForm
from tmdb.shortcuts import search_shows, retrieve_show
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.http import HttpResponse

from series.models import APIShow


# Create your views here.


class SearchSeriesView(FormView):
    """Search for series."""
    template_name = 'series/search_series.html'
    form_class = SearchSeriesForm
    success_url = '/search'

    def get_success_url(self) -> str:
        return reverse(
            'search_results',
            kwargs={'term': self.request.POST['search_term']}
        )


class SearchResultsView(View):
    """Result page after a search by user"""
    template = 'series/search_results.html'

    def get(self, request, term: str):
        shows = search_shows(term)
        return render(
            template_name='series/search_results.html',
            request=request,
            context={'shows_list': shows, 'search_term': term}
        )


class ShowDetailsView(View):
    """Details of a show"""
    template = 'series/show_details.html'

    def get(self, request, id: int):
        show = retrieve_show(id)
        sub = APIShow.objects.follows(show_id=id, user=request.user)
        return render(
            template_name='series/show_details.html',
            request=request,
            context={'show': show, 'is_subscribed': sub, 'user': request.user}
        )


class FollowedSeriesView(LoginRequiredMixin, ListView):
    """Page to display the followed series of a user."""
    template_name = 'series/followed_series.html'
    context_object_name = 'followed_series_list'

    def get_queryset(self):
        return APIShow.objects.filter(followers=self.request.user)


class APISubscribe(View):
    """View called when a user subscribes or unsubscribes to a new show

    """

    def post(self, request, show_id: int):
        """Called when a POST request is made to subscribe the user to the show
        Adds the user to the followers list of the show

        """
        try:
            show = APIShow.objects.get(id=show_id)
        except APIShow.DoesNotExist:
            show = APIShow.objects.create_from_api(show_id)
        show.followers.add(request.user)
        return HttpResponse(200)

    def delete(self, request, show_id: int):
        """Called when a DELETE request is made to unsubscribe the user from the show
        Removes the user from the followers list of the show

        """
        show = APIShow.objects.filter(id=show_id).first()
        show.followers.remove(request.user)
        return HttpResponse(200)
