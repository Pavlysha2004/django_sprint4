from django.shortcuts import render
from django.http import Http404
from .models import Category, Post, Comment
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User
from .forms import ProfileEditForm, PostCreateForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.views.generic import (
    ListView, CreateView
)
# , DeleteView, ,,DetailView UpdateView
from django.urls import reverse_lazy


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostCreateForm
    template_name = 'blog/create.html'
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'user_name': self.request.user.username}
        )


def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if not request.user.is_authenticated:
        return redirect('blog:post_detail', post_id=post.id)

    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostCreateForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostCreateForm(instance=post)

    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_profile(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.user != user:
        return redirect('blog:profile', profile_id=request.user.id)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST or None, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', user_name=user.username)
    else:
        form = ProfileEditForm(instance=user)

    return render(request, 'blog/user.html', {'form': form})

# def index(request):
#     template_name = 'blog/index.html'
#     post_list = Post.objects.filter(
#         pub_date__lt=timezone.now(),
#         is_published__exact=True,
#         category__is_published=True).order_by('-pub_date')[:5]
#     context = {'post_list': post_list}
#     return render(request, template_name, context)


class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    queryset = Post.objects.filter(
        pub_date__lte=timezone.now(),
        is_published__exact=True,
        category__is_published=True)
    ordering = '-pub_date'
    paginate_by = 10


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        now = timezone.now()
        if post.pub_date > now or not post.is_published or (
                post.category and not post.category.is_published):
            raise Http404()
    comments = Comment.objects.filter(post=post)
    form = CommentForm() if request.user.is_authenticated else None
    template_name = 'blog/detail.html'
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, template_name, context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category, slug=category_slug, is_published=True)
    now = timezone.now()
    post_list = Post.objects.filter(
        category__exact=category,
        is_published__exact=True,
        pub_date__lt=now
    ).order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template_name = 'blog/category.html'
    context = {
        'category': category,
        'page_obj': page_obj
    }

    return render(request, template_name, context)


def profile(request, user_name):
    user_inf = get_object_or_404(User, username=user_name)

    if request.user == user_inf:
        post_list = Post.objects.filter(author=user_inf).order_by('-pub_date')
    else:
        post_list = Post.objects.filter(
            author=user_inf,
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': user_inf,
        'page_obj': page_obj
    }
    return render(request, 'blog/profile.html', context)


@login_required
def add_comment(request, post_id):

    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment
    })


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', user_name=request.user.username)

    form = PostCreateForm(request.POST, instance=post)
    return render(request, 'blog/create.html', {
        'form': form
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, 'blog/comment.html', {
        'comment': comment
    })
