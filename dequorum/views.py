from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .forms import ThreadCreateForm, MessageCreateForm, TagFilterForm
from .models import Thread


def thread_list(request):
    threads = Thread.objects.visible()
    tag_form = TagFilterForm(request.GET)
    if tag_form.is_valid():
        threads = threads.filter(tags__in=tag_form.cleaned_data['tag'])

    return render(request, 'dequorum/thread_list.html', {
        'threads': threads,
        'tag_form': tag_form,
    })


@login_required
def thread_create(request):

    if request.method == 'POST':
        thread_form = ThreadCreateForm(request.POST)
        message_form = MessageCreateForm(request.POST)
        if all([thread_form.is_valid(), message_form.is_valid()]):
            thread = thread_form.save(commit=False)
            thread.owner = request.user
            thread.save()

            message = message_form.save(commit=False)
            message.author = request.user
            message.thread = thread
            message.save()

            return redirect(thread)
    else:
        thread_form = ThreadCreateForm()
        message_form = MessageCreateForm()

    return render(request, 'dequorum/thread_create.html', {
        'thread_form': thread_form,
        'message_form': message_form,
    })


def thread_detail(request, thread_pk):
    thread = get_object_or_404(Thread.objects.visible(), pk=thread_pk)

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
        'messages': thread.messages.visible(),
        'form': form,
    })
