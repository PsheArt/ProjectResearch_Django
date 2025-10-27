from django.urls import path
from .views import research_list, create_research, rate_aspect, get_average_scores, view_ratings, home, research_detail, my_researches, research_detail_not, search_experts
from django.conf import settings

urlpatterns = [
    path('', home, name='home'),
    path('research/', research_list, name='research_list'),
    path('research/create/', create_research, name='create_research'),
    path('research/rate/<int:aspect_id>/', rate_aspect, name='rate_aspect'),
    path('research/<int:research_id>/ratings/', view_ratings, name='view_ratings'),
    path('research/get_average_scores/<int:aspect_id>/', get_average_scores, name='get_average_scores'),
    path('research/<int:research_id>/', research_detail, name='research_detail'),
    path('research/research<int:research_id>/', research_detail_not, name='research_details'),
    path('my_researches/', my_researches, name='my_researches'),
    path('search_experts/', search_experts, name='search_experts'),

]