from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST
from users.decorators import role_required
from .models import Book, Author, Category, Publisher, BookCopy, DigitalResource, BookReview
from django.core.paginator import Paginator

# ==================== READER SIDE ====================


@login_required
def book_list(request):
    books = Book.objects.all().select_related('author', 'category').order_by('title')
    categories = Category.objects.all()

    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__author_name__icontains=query) |
            Q(isbn__icontains=query)
        )

    if category_id:
        books = books.filter(category_id=category_id)

    # Pagination - 8 books per page
    paginator = Paginator(books, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'books': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    }
    return render(request, 'books/book_list.html', context)


@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    available_copies = book.copies.filter(status='Available')

    reviews = book.reviews.select_related('user').order_by('-created_at')
    my_review = reviews.filter(user=request.user).first()
    other_reviews = reviews.exclude(user=request.user) if my_review else reviews

    related_books = Book.objects.filter(
        category=book.category
    ).exclude(id=book.id).select_related('author')[:4] if book.category else []

    digital_resources = book.digital_resources.all()

    context = {
        'book': book,
        'available_copies': available_copies,
        'my_review': my_review,
        'other_reviews': other_reviews,
        'related_books': related_books,
        'digital_resources': digital_resources,
    }
    return render(request, 'books/book_detail.html', context)


def _update_average_rating(book):
    avg = book.reviews.aggregate(avg=Avg('rating'))['avg']
    book.average_rating = round(avg, 2) if avg is not None else 0.00
    book.save(update_fields=['average_rating'])


@login_required
@require_POST
def add_review(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    try:
        rating = int(request.POST.get('rating', ''))
        if rating < 1 or rating > 5:
            raise ValueError
    except (TypeError, ValueError):
        messages.error(request, "Please choose a rating between 1 and 5 stars.")
        return redirect('books:book_detail', book_id=book.id)

    comment = request.POST.get('comment', '').strip()

    review, created = BookReview.objects.update_or_create(
        book=book, user=request.user,
        defaults={'rating': rating, 'comment': comment}
    )
    _update_average_rating(book)

    messages.success(request, "Thanks for your review!" if created else "Your review was updated.")
    return redirect('books:book_detail', book_id=book.id)


@login_required
@require_POST
def delete_review(request, review_id):
    review = get_object_or_404(BookReview, id=review_id, user=request.user)
    book = review.book
    review.delete()
    _update_average_rating(book)
    messages.success(request, "Your review was removed.")
    return redirect('books:book_detail', book_id=book.id)


@login_required
def download_digital_resource(request, resource_id):
    resource = get_object_or_404(DigitalResource, id=resource_id)

    if not resource.file:
        raise Http404("This resource has no file attached.")

    resource.download_count += 1
    resource.save(update_fields=['download_count'])

    return FileResponse(
        resource.file.open('rb'),
        as_attachment=True,
        filename=resource.file.name.rsplit('/', 1)[-1],
    )


# ==================== PHASE 6: BOOK MANAGEMENT (Staff) ====================
@login_required
@role_required('Admin', 'Librarian')
def manage_books(request):
    books = Book.objects.select_related('author', 'category', 'publisher').all()

    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(isbn__icontains=query) |
            Q(author__author_name__icontains=query)
        )

    if category_id:
        books = books.filter(category_id=category_id)

    categories = Category.objects.all()

    context = {
        'books': books,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
    }
    return render(request, 'books/manage_books.html', context)


@login_required
@role_required('Admin', 'Librarian')
def add_book(request):
    authors = Author.objects.all()
    categories = Category.objects.all()
    publishers = Publisher.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        isbn = request.POST.get('isbn')
        author_id = request.POST.get('author')
        category_id = request.POST.get('category')
        publisher_id = request.POST.get('publisher')
        publication_year = request.POST.get('publication_year')
        language = request.POST.get('language', 'English')
        total_copies = int(request.POST.get('total_copies', 1))
        summary = request.POST.get('summary')
        cover_image = request.FILES.get('cover_image')

        book = Book.objects.create(
            title=title,
            isbn=isbn,
            author_id=author_id if author_id else None,
            category_id=category_id if category_id else None,
            publisher_id=publisher_id if publisher_id else None,
            publication_year=publication_year if publication_year else None,
            language=language,
            total_copies=total_copies,
            available_copies=total_copies,
            summary=summary,
            cover_image=cover_image
        )

        # Create physical copies
        for i in range(total_copies):
            BookCopy.objects.create(
                book=book,
                barcode=f"{book.id}-{i+1:03d}",
                status='Available'
            )

        messages.success(request, f"Book '{book.title}' added successfully!")
        return redirect('books:manage_books')

    context = {
        'authors': authors,
        'categories': categories,
        'publishers': publishers,
    }
    return render(request, 'books/add_book.html', context)


@login_required
@role_required('Admin', 'Librarian')
def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    authors = Author.objects.all()
    categories = Category.objects.all()
    publishers = Publisher.objects.all()

    if request.method == 'POST':
        book.title = request.POST.get('title')
        book.isbn = request.POST.get('isbn')
        book.author_id = request.POST.get('author') or None
        book.category_id = request.POST.get('category') or None
        book.publisher_id = request.POST.get('publisher') or None
        book.publication_year = request.POST.get('publication_year') or None
        book.language = request.POST.get('language', 'English')
        book.summary = request.POST.get('summary')

        if request.FILES.get('cover_image'):
            book.cover_image = request.FILES.get('cover_image')

        book.save()
        messages.success(request, "Book updated successfully!")
        return redirect('books:manage_books')

    context = {
        'book': book,
        'authors': authors,
        'categories': categories,
        'publishers': publishers,
    }
    return render(request, 'books/edit_book.html', context)


@login_required
@role_required('Admin', 'Librarian')
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f"Book '{title}' deleted successfully!")
        return redirect('books:manage_books')

    return render(request, 'books/delete_book.html', {'book': book})


# ==================== MANAGE AUTHORS ====================
@login_required
@role_required('Admin', 'Librarian')
def manage_authors(request):
    authors = Author.objects.all().order_by('author_name')
    query = request.GET.get('q', '')
    if query:
        authors = authors.filter(author_name__icontains=query)
    return render(request, 'books/manage_authors.html', {'authors': authors, 'query': query})


@login_required
@role_required('Admin', 'Librarian')
def add_author(request):
    if request.method == 'POST':
        name = request.POST.get('author_name')
        biography = request.POST.get('biography', '')
        country = request.POST.get('country', '')
        Author.objects.create(author_name=name, biography=biography, country=country)
        messages.success(request, "Author added successfully!")
        return redirect('books:manage_authors')
    return render(request, 'books/add_author.html')


@login_required
@role_required('Admin', 'Librarian')
def edit_author(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    if request.method == 'POST':
        author.author_name = request.POST.get('author_name')
        author.biography = request.POST.get('biography', '')
        author.country = request.POST.get('country', '')
        author.save()
        messages.success(request, "Author updated successfully!")
        return redirect('books:manage_authors')
    return render(request, 'books/edit_author.html', {'author': author})


@login_required
@role_required('Admin', 'Librarian')
def delete_author(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    if request.method == 'POST':
        author.delete()
        messages.success(request, "Author deleted successfully!")
        return redirect('books:manage_authors')
    return render(request, 'books/delete_author.html', {'author': author})


# ==================== MANAGE CATEGORIES ====================
@login_required
@role_required('Admin', 'Librarian')
def manage_categories(request):
    categories = Category.objects.all().order_by('category_name')
    return render(request, 'books/manage_categories.html', {'categories': categories})


@login_required
@role_required('Admin', 'Librarian')
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('category_name')
        description = request.POST.get('description', '')
        Category.objects.create(category_name=name, description=description)
        messages.success(request, "Category added successfully!")
        return redirect('books:manage_categories')
    return render(request, 'books/add_category.html')


@login_required
@role_required('Admin', 'Librarian')
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.category_name = request.POST.get('category_name')
        category.description = request.POST.get('description', '')
        category.save()
        messages.success(request, "Category updated successfully!")
        return redirect('books:manage_categories')
    return render(request, 'books/edit_category.html', {'category': category})


@login_required
@role_required('Admin', 'Librarian')
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully!")
        return redirect('books:manage_categories')
    return render(request, 'books/delete_category.html', {'category': category})


# ==================== MANAGE PUBLISHERS ====================
@login_required
@role_required('Admin', 'Librarian')
def manage_publishers(request):
    publishers = Publisher.objects.all().order_by('publisher_name')
    return render(request, 'books/manage_publishers.html', {'publishers': publishers})


@login_required
@role_required('Admin', 'Librarian')
def add_publisher(request):
    if request.method == 'POST':
        name = request.POST.get('publisher_name')
        address = request.POST.get('address', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        Publisher.objects.create(publisher_name=name, address=address, phone=phone, email=email)
        messages.success(request, "Publisher added successfully!")
        return redirect('books:manage_publishers')
    return render(request, 'books/add_publisher.html')


@login_required
@role_required('Admin', 'Librarian')
def edit_publisher(request, publisher_id):
    publisher = get_object_or_404(Publisher, id=publisher_id)
    if request.method == 'POST':
        publisher.publisher_name = request.POST.get('publisher_name')
        publisher.address = request.POST.get('address', '')
        publisher.phone = request.POST.get('phone', '')
        publisher.email = request.POST.get('email', '')
        publisher.save()
        messages.success(request, "Publisher updated successfully!")
        return redirect('books:manage_publishers')
    return render(request, 'books/edit_publisher.html', {'publisher': publisher})


@login_required
@role_required('Admin', 'Librarian')
def delete_publisher(request, publisher_id):
    publisher = get_object_or_404(Publisher, id=publisher_id)
    if request.method == 'POST':
        publisher.delete()
        messages.success(request, "Publisher deleted successfully!")
        return redirect('books:manage_publishers')
    return render(request, 'books/delete_publisher.html', {'publisher': publisher})

# ==================== DIGITAL RESOURCES (PDF / Journal) ====================

@login_required
@role_required('Admin', 'Librarian')
def manage_digital_resources(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    resources = DigitalResource.objects.filter(book=book)
    return render(request, 'books/manage_digital.html', {
        'book': book,
        'resources': resources
    })


@login_required
@role_required('Admin', 'Librarian')
def upload_digital_resource(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        file = request.FILES.get('file')
        file_type = request.POST.get('file_type', 'pdf')
        access_level = request.POST.get('access_level', 'Member')

        if file:
            DigitalResource.objects.create(
                book=book,
                file=file,
                file_type=file_type,
                access_level=access_level
            )
            messages.success(request, "Digital resource uploaded successfully!")
            return redirect('books:manage_digital', book_id=book.id)
        else:
            messages.error(request, "Please select a file to upload.")

    return render(request, 'books/upload_digital.html', {'book': book})


@login_required
@role_required('Admin', 'Librarian')
def delete_digital_resource(request, resource_id):
    resource = get_object_or_404(DigitalResource, id=resource_id)
    book_id = resource.book.id

    if request.method == 'POST':
        resource.delete()
        messages.success(request, "Digital resource deleted successfully!")
        return redirect('books:manage_digital', book_id=book_id)

    return render(request, 'books/delete_digital.html', {'resource': resource})


@login_required
def live_search_books(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'title')  # default sort

    books = Book.objects.select_related('author', 'category').all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__author_name__icontains=query) |
            Q(isbn__icontains=query)
        )

    if category_id:
        books = books.filter(category_id=category_id)

    # Sorting
    if sort_by == 'title':
        books = books.order_by('title')
    elif sort_by == 'title_desc':
        books = books.order_by('-title')
    elif sort_by == 'available':
        books = books.order_by('-available_copies')
    elif sort_by == 'newest':
        books = books.order_by('-id')  # newest first
    else:
        books = books.order_by('title')

    results = []
    for book in books[:30]:
        results.append({
            'id': book.id,
            'title': book.title,
            'author': book.author.author_name if book.author else 'Unknown',
            'category': book.category.category_name if book.category else 'General',
            'available': book.available_copies,
            'url': f'/books/{book.id}/'
        })

    return JsonResponse({'books': results})