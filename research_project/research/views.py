from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from research_project.settings import EMAIL_HOST_USER
from .forms import ResearchForm, AspectForm, ParameterForm, RatingForm
from django.db.models import Avg

from .models import Rating, Research, Aspect, Parameter, ResultResearch
from django.core.mail import send_mail
from django.contrib import messages
from django.http import JsonResponse

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

def home(request):
    researches = Research.objects.all().prefetch_related('ratings') 
    for research in researches:
        research.average_rating = round(research.ratings.aggregate(Avg('score'))['score__avg'] or 0, 3)  if research.average_rating is not None else 0
       
    return render(request, 'index.html', {'researches': researches})

@login_required
def research_list(request):
    researches = Research.objects.all()
    paginator = Paginator(researches, 1)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    rated_research_ids = set()
    for research in researches:
        average_score = research.ratings.aggregate(Avg('score')).get('score__avg', 0)
        research.average_rating = round(average_score, 3) if average_score is not None else 0
    if request.user.is_authenticated:
        user_ratings = request.user.rating_set.all()
        rated_research_ids = set(rating.research.id for rating in request.user.rating_set.all())
    context = {
        'researches': researches,
        'user_ratings': user_ratings,
        'rated_research_ids': rated_research_ids,
        'page_obj': page_obj

    }
    return render(request, 'research/research_list.html', context)

@login_required
def create_research(request):
    if request.method == 'POST':
        form = ResearchForm(request.POST, request.FILES)
        if form.is_valid():
            research = form.save()
            research.author = request.user 
            participants_ids = request.POST.get('participants', '').split(',')
            participants_ids = [id for id in participants_ids if id.isdigit()] 
            print(participants_ids)
            if participants_ids:  
                participants = User.objects.filter(id__in=participants_ids)
                research.participants.set(participants) 
                research.save()
            aspects_data = request.POST.getlist('aspect_name')
            stages_data = request.POST.getlist('stage_number')     
            last_stage = 0
            for i in range(len(aspects_data)):
                aspect_form = AspectForm({'name': aspects_data[i], 'stage_number': stages_data[i]})
                if aspect_form.is_valid():
                    aspect = aspect_form.save(commit=False)
                    aspect.research = research
                    aspect.save()
                    param_data = request.POST.getlist(f'parameter_name_[{i + 1}]')
                    last_stage +=1
                    for param_name in param_data:
                        if param_name:
                            parameter_form = ParameterForm({'name': param_name})
                            if parameter_form.is_valid():
                                parameter = parameter_form.save(commit=False)
                                parameter.aspect = aspect
                                parameter.save()
                            else:
                                messages.error(request, f'Ошибка в параметре: {parameter_form.errors}')
                else:
                    messages.error(request, f'Ошибка в аспекте: {aspect_form.errors}')
            result =ResultResearch.objects.create(
                research = research,
                user = request.user,
                name = "Подведите итоги исследования"
            )
            
            messages.success(request, 'Исследование создано и участники уведомлены.')
            return redirect('research_list')
        else:
            messages.error(request, f'Ошибка в основном формуляре: {form.errors}')
    else:
        form = ResearchForm()
    return render(request, 'research/create_research.html', {'form': form})

def search_experts(request):
    query = request.GET.get('q', '')
    experts = User.objects.filter(username__icontains=query)[:3]  
    results = [{'id': expert.id, 'name': expert.username} for expert in experts]
    return JsonResponse(results, safe=False)

@login_required
def rate_aspect(request, aspect_id):
    research = Research.objects.get(pk=aspect_id)
    aspects = Aspect.objects.filter(research=research)
    max_stage = aspects.last().stage_number+1
    existing_ratings = Rating.objects.filter(user=request.user, parameter__aspect__research=research)
    existing_ratings_by_aspect = 0
    ratings_dict = {rating.parameter.id: rating.score for rating in existing_ratings}
    results = ResultResearch.objects.filter(research=research).first()
    if request.method == 'POST':
        for aspect in aspects:
            existing_ratings_by_aspect = Rating.objects.filter(parameter__aspect = aspect)
            print(existing_ratings_by_aspect)
            for param in aspect.parameters.all():
                score = request.POST.get(f'score_{param.id}')
                if score:
                    Rating.objects.create(research = research, user=request.user, parameter=param, score=int(score))
        resTXT = request.POST.get(f'results_{results.id}')
     
        results.result_value = resTXT
        results.save()
        
        unique_users_count = Rating.objects.filter(parameter__aspect__research=research).values('user').distinct().count()
        total_experts_count = research.participants.count() 
        if unique_users_count >= total_experts_count:
            research.is_completed = True
            research.save()

        messages.success(request, 'Оценка успешно сохранена.')
        return render(request, 'research/rate_aspect.html', {'research': research, 'aspects': aspects, 'ratings_dict': ratings_dict, 'results':results})
    
    return render(request, 'research/rate_aspect.html', {'research': research, 'aspects': aspects, 'ratings_dict': ratings_dict, 'results':results, 'max_stage':max_stage})

def view_ratings(request, research_id):
    research = get_object_or_404(Research, id=research_id)
    user_ratings = Rating.objects.filter(user=request.user, parameter__aspect__research=research)

    if request.method == 'POST':
        for rating in user_ratings:
            new_score = request.POST.get(f'score_{rating.parameter.id}')
            if new_score:
                rating.score = new_score
                rating.save()
        
        return redirect('view_ratings', research_id=research.id)

    return render(request, 'research/view_ratings.html', {
        'research': research,
        'user_ratings': user_ratings,
    })
def get_average_scores(request, aspect_id):
    aspect = Aspect.objects.get(pk=aspect_id)
    parameters = aspect.parameters.all()
 
    scores = {param.name: Rating.average_score(param) for param in parameters}
    
    return JsonResponse(scores)

def research_detail(request, research_id):
    research = get_object_or_404(Research, id=research_id)
    aspects = research.aspects.all()
    aspects_with_avg = []
    user_ratings = {}
    all_scores = []
    experts = research.participants.all()
    rating_expet = ''
    result = research.resultResearch.all()
    for expert in experts:
        ratings = expert.rating_set.filter(research=research)
        if ratings:
            average_score_experts = round(sum([rating.score for rating in ratings]) / len(ratings), 3)
            rating_expet += f"{expert.username} - cредняя оценка по исследованию: {average_score_experts}\n"
    rating_expet = rating_expet.rstrip('\n')
    for aspect in aspects:
        parameters = aspect.parameters.all()
        for parameter in parameters:
            scores = parameter.rating_set.values_list('score', flat=True)
            all_scores.extend(scores)
            parameter_ratings = parameter.rating_set.all()
            for rating in parameter_ratings:
                user_id = rating.user.id
                user_name = rating.user.username
                if user_id not in user_ratings:
                    user_ratings[user_id] = {
                        'name': user_name,
                        'ratings': {}
                    }
                if aspect.id not in user_ratings[user_id]['ratings']:
                    user_ratings[user_id]['ratings'][aspect.id] = {
                        'aspect_name': aspect.name,
                        'parameters': {}
                    }              
                user_ratings[user_id]['ratings'][aspect.id]['parameters'][parameter.id] = rating.score
        if all_scores:
            average_score = round(sum(all_scores) / len(all_scores), 3)
        else:
            average_score = 0
        aspects_with_avg.append({
            'aspect': aspect,
            'parameters': parameters,
            'average_score': average_score,
        })
    average_rating = round(research.ratings.aggregate(Avg('score'))['score__avg'] or 0, 3)
    is_editable = not research.is_completed
    existing_ratings = Rating.objects.filter(user=request.user, parameter__aspect__research=research)
    ratings_dict = {rating.parameter.id: rating.score for rating in existing_ratings}
    unique_users_count = Rating.objects.filter(parameter__aspect__research=research).values('user').distinct().count()
    total_experts_count = research.participants.count() 
    print(rating_expet)
    if unique_users_count >= total_experts_count:
        research.is_completed = True
        research.save()
    return render(request, 'research/research_detail.html', {
        'research': research,
        'aspects': aspects,
        'ratings_dict':ratings_dict,
        'aspects_with_avg': aspects_with_avg,
        'user_ratings': user_ratings,
        'average_rating': average_rating,
        'rating_expet': rating_expet,
        'is_editable': is_editable,
    })

def research_detail_not(request, research_id):
    research = get_object_or_404(Research, id=research_id)
    aspects = research.aspects.all()
    average_rating = research.ratings.aggregate(Avg('score'))['score__avg'] or 0
    is_editable = not research.is_completed
    existing_ratings = Rating.objects.filter(parameter__aspect__research=research)
    return render(request, 'research/research_detail.html', {
        'research': research,
        'aspects': aspects,
        'average_rating': average_rating,
        'is_editable': is_editable,
    })

def my_researches(request):
    researches = Research.objects.filter(author=request.user)
    return render(request, 'research/my_research.html', {'researches': researches})