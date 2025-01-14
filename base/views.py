from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Room, Topic, Message, RoomCount
from .forms import RoomForm, UserForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q


def home(request):
    q = request.GET.get('q') if request.GET.get('q') is not None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(description__icontains=q) |
        Q(name__icontains=q)
    )
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    topics = Topic.objects.all()[0:5]
    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count,
               'room_messages': room_messages}
    return render(request, 'base/home.html', context)


def room_page(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}
    return render(request, 'base/room.html', context)


def login_page(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User does not exist!')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'User or password does not exist')
    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def register_page(request):
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during the registration')

    context = {'form': form}
    return render(request, 'base/login_register.html', context)


def logout_user(request):
    logout(request)
    return redirect('home')


def user_profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms,
               'room_messages': room_messages,
               'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    all_topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        # Если топик существует
        if created is False:
            room_count = RoomCount.objects.get(topic_id=topic.id)
            room_count.room_count += 1
            room_count.save()
        else:
            RoomCount.objects.create(
                topic=topic,
                room_count=1
            )

        return redirect('home')

    context = {'form': form, 'all_topics': all_topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def update_room(request, pk):

    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        form = RoomForm(request.POST, instance=room)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form': form, 'topic': topics,
               'room': room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def delete(request, pk):
    room = Room.objects.get(id=pk)
    topic = room.topic

    topic_id = Room.objects.get(id=pk).topic_id
    room_count = RoomCount.objects.get(topic_id=topic_id).room_count

    if request.user != room.host:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        if room_count > 1:
            room.delete()
            room_count = RoomCount.objects.get(topic_id=topic.id)
            room_count.room_count -= 1
            room_count.save()
            return redirect('home')
        elif room_count == 1:
            topic.delete()
            return redirect('home')
        else:
            return HttpResponse('room_count < 1 or Null')
    context = {'obj': room, 'topic': topic, 'room': room,
               'topic_id': topic_id, 'room_count': room_count}
    return render(request, 'base/delete.html', context)


@login_required(login_url='login')
def delete_message(request, pk):

    message = Message.objects.get(id=pk)
    if request.user != message.user:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')

    context = {'obj': message}
    return render(request, 'base/delete.html', context)


def strange_things(request):

    name = request.user
    context = {'name': name}
    return render(request, 'base/strange_things.html', context)


@login_required(login_url='login')
def update_user(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    return render(request, 'base/update_user.html', {'form': form})


def topics_page(request):
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    topics = Topic.objects.filter(name__icontains=q)
    context = {'topics': topics}
    return render(request, 'base/topics.html', context)


def activity_page(request):
    room_messages = Message.objects.all()
    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context)
