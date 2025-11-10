from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Prefetch
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User

from .forms import ResearchForm, AspectForm, ParameterForm
from .models import Research, Aspect, Parameter, Rating, ResearchResult  # Обратите внимание: ResultResearch → ResearchResult


# ----------------------------
# Views
# ----------------------------

def home(request):
    researches = (
        Research.objects
        .prefetch_related(
            Prefetch('ratings', queryset=Rating.objects.select_related('user', 'parameter'))
        )
        .annotate(average_rating=Avg('ratings__score'))
    )
    return render(request, 'index.html', {'researches': researches})


@login_required
def research_list(request):
    researches = (
        Research.objects
        .annotate(average_rating=Avg('ratings__score'))
        .prefetch_related('participants')
    )

    # Пагинация
    paginator = Paginator(researches, 1)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Получаем ID исследований, уже оценённых пользователем
    rated_research_ids = set(
        Rating.objects.filter(user=request.user).values_list('research_id', flat=True)
    )

    context = {
        'page_obj': page_obj,
        'rated_research_ids': rated_research_ids,
    }
    return render(request, 'research/research_list.html', context)


@login_required
def create_research(request):
    if request.method == 'POST':
        form = ResearchForm(request.POST, request.FILES)
        if form.is_valid():
            research = form.save(commit=False)
            research.author = request.user
            research.save()

            # Участники
            participant_ids = [pid for pid in request.POST.get('participants', '').split(',') if pid.isdigit()]
            if participant_ids:
                participants = User.objects.filter(id__in=participant_ids)
                research.participants.set(participants)

            # Аспекты и параметры
            aspect_names = request.POST.getlist('aspect_name')
            stage_numbers = request.POST.getlist('stage_number')

            for i, (name, stage) in enumerate(zip(aspect_names, stage_numbers)):
                aspect_form = AspectForm({'name': name, 'stage_number': stage})
                if not aspect_form.is_valid():
                    messages.error(request, f"Ошибка в аспекте {i+1}: {aspect_form.errors}")
                    continue

                aspect = aspect_form.save(commit=False)
                aspect.research = research
                aspect.save()

                param_names = request.POST.getlist(f'parameter_name_[{i + 1}]')
                for param_name in param_names:
                    if not param_name.strip():
                        continue
                    param_form = ParameterForm({'name': param_name})
                    if param_form.is_valid():
                        param = param_form.save(commit=False)
                        param.aspect = aspect
                        param.save()
                    else:
                        messages.error(request, f"Ошибка в параметре '{param_name}': {param_form.errors}")

            # Создаём результат
            ResearchResult.objects.create(
                research=research,
                user=request.user,
                name="Подведите итоги исследования"
            )

            messages.success(request, 'Исследование создано и участники уведомлены.')
            return redirect('research_list')
        else:
            messages.error(request, f'Ошибка в форме: {form.errors}')

    form = ResearchForm()
    return render(request, 'research/create_research.html', {'form': form})


def search_experts(request):
    query = request.GET.get('q', '').strip()
    experts = User.objects.filter(username__icontains=query)[:3]
    results = [{'id': u.id, 'name': u.username} for u in experts]
    return JsonResponse(results, safe=False)


@login_required
def rate_aspect(request, research_id):
    research = get_object_or_404(Research, id=research_id)
    aspects = research.aspects.prefetch_related('parameters').all()
    results = research.results.first()  # related_name='results' из ResearchResult

    existing_ratings = Rating.objects.filter(user=request.user, research=research)
    ratings_dict = {rating.parameter_id: rating.score for rating in existing_ratings}

    if request.method == 'POST':
        # Сохраняем оценки
        for aspect in aspects:
            for param in aspect.parameters.all():
                score = request.POST.get(f'score_{param.id}')
                if score and score.isdigit():
                    Rating.objects.update_or_create(
                        user=request.user,
                        parameter=param,
                        defaults={'score': int(score), 'research': research}
                    )

        # Сохраняем итоговый текст
        if results:
            res_text = request.POST.get(f'results_{results.id}', '').strip()
            results.result_value = res_text
            results.save()

        # Проверка завершения
        unique_raters = Rating.objects.filter(research=research).values('user').distinct().count()
        if unique_raters >= research.participants.count() and research.participants.exists():
            research.is_completed = True
            research.save()

        messages.success(request, 'Оценка успешно сохранена.')
        return redirect('research_detail', research_id=research.id)

    max_stage = aspects.last().stage_number + 1 if aspects.exists() else 1
    return render(request, 'research/rate_aspect.html', {
        'research': research,
        'aspects': aspects,
        'ratings_dict': ratings_dict,
        'results': results,
        'max_stage': max_stage
    })


@login_required
def view_ratings(request, research_id):
    research = get_object_or_404(Research, id=research_id)
    user_ratings = Rating.objects.filter(user=request.user, research=research)

    if request.method == 'POST':
        for rating in user_ratings:
            score = request.POST.get(f'score_{rating.parameter.id}')
            if score and score.isdigit():
                rating.score = int(score)
                rating.save()
        return redirect('view_ratings', research_id=research.id)

    return render(request, 'research/view_ratings.html', {
        'research': research,
        'user_ratings': user_ratings,
    })


def get_average_scores(request, aspect_id):
    aspect = get_object_or_404(Aspect, id=aspect_id)
    scores = {}
    for param in aspect.parameters.all():
        avg = param.rating_set.aggregate(avg=Avg('score'))['avg']
        scores[param.name] = round(avg, 1) if avg is not None else 0
    return JsonResponse(scores)


@login_required
def research_detail(request, research_id):
    research = get_object_or_404(
        Research.objects.annotate(average_rating=Avg('ratings__score')),
        id=research_id
    )

    # Оптимизированный запрос с предзагрузкой
    aspects = (
        research.aspects
        .prefetch_related(
            Prefetch('parameters', queryset=Parameter.objects.prefetch_related('rating_set__user'))
        )
        .order_by('stage_number')
    )

    # Собираем оценки по экспертам и параметрам
    user_ratings = {}
    expert_averages = []

    for expert in research.participants.all():
        expert_ratings = expert.rating_set.filter(research=research)
        if expert_ratings:
            avg = expert_ratings.aggregate(Avg('score'))['score__avg']
            expert_averages.append(f"{expert.username} - средняя оценка по исследованию: {round(avg, 3)}")

    # Структура для отображения в шаблоне
    aspects_with_avg = []
    for aspect in aspects:
        all_scores = []
        for param in aspect.parameters.all():
            scores = [r.score for r in param.rating_set.all()]
            all_scores.extend(scores)
        avg = round(sum(all_scores) / len(all_scores), 3) if all_scores else 0
        aspects_with_avg.append({'aspect': aspect, 'average_score': avg})

    # Проверка завершённости
    unique_raters = Rating.objects.filter(research=research).values('user').distinct().count()
    if unique_raters >= research.participants.count() and research.participants.exists():
        research.is_completed = True
        research.save()

    # Для формы редактирования
    ratings_dict = {
        r.parameter_id: r.score
        for r in Rating.objects.filter(user=request.user, research=research)
    }

    context = {
        'research': research,
        'aspects': aspects,
        'aspects_with_avg': aspects_with_avg,
        'user_ratings': user_ratings,
        'rating_expet': '\n'.join(expert_averages),
        'is_editable': not research.is_completed,
        'ratings_dict': ratings_dict,
        'results': research.results.first(),
    }
    return render(request, 'research/research_detail.html', context)


@login_required
def my_researches(request):
    researches = Research.objects.filter(author=request.user).annotate(
        average_rating=Avg('ratings__score')
    )
    return render(request, 'research/my_research.html', {'researches': researches})