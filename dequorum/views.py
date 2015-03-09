from django.contrib.auth.decorators import login_required
from django.db.models import Count, Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import ThreadCreateForm, MessageCreateForm, TagFilterForm
from .models import Thread, Message


def thread_list(request, path_tags=''):
    threads = Thread.objects.visible()

    # Select tags - AND
    selected_tags = [
        tag
        for tag in (tag.strip() for tag in path_tags.split('/'))
        if tag
    ]
    for tag in selected_tags:
        threads = threads.filter(tags__name=tag)

    # Search tags - OR
    tag_form = TagFilterForm(request.GET)
    if tag_form.is_valid():
        tag_qset = tag_form.cleaned_data['tag']
        if tag_qset.count():
                threads = threads.filter(tags__in=tag_form.cleaned_data['tag'])

    paginator = Paginator(threads, 10)
    page_num = request.GET.get('page')

    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return render(request, 'dequorum/thread_list.html', {
        'tag_form': tag_form,
        'page': page,
    })


@login_required
def thread_create(request):

    if request.method == 'POST':
        thread_form = ThreadCreateForm(request.POST)
        message_form = MessageCreateForm(request.POST)
        tag_form = TagFilterForm(request.POST)
        if all([thread_form.is_valid(), message_form.is_valid(), tag_form.is_valid()]):
            thread = thread_form.save(commit=False)
            thread.owner = request.user
            thread.save()
            thread.tags.add(*list(tag_form.cleaned_data['tag']))
            thread.save()

            message = message_form.save(commit=False)
            message.author = request.user
            message.thread = thread
            message.save()

            return redirect(thread)
    else:
        thread_form = ThreadCreateForm()
        message_form = MessageCreateForm()
        tag_form = TagFilterForm()

    return render(request, 'dequorum/thread_create.html', {
        'thread_form': thread_form,
        'message_form': message_form,
        'tag_form': tag_form,
    })


def thread_detail(request, thread_pk):
    thread_qs = (Thread.objects
        .visible()
        .annotate(message_count=Count('messages'))
        .prefetch_related(Prefetch('messages', Message.objects.visible().select_related('author')))
    )
    thread = get_object_or_404(thread_qs, pk=thread_pk)

    if request.user.is_authenticated():
        if request.method == 'POST':
            form = MessageCreateForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.author = request.user
                obj.thread = thread
                obj.save()
                return redirect(thread)

        else:
            form = MessageCreateForm()

    else:
        form = None

    return render(request, 'dequorum/thread_detail.html', {
        'thread': thread,
        'messages': thread.messages.all(),
        'form': form,
    })
