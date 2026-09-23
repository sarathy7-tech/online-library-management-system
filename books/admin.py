from django.contrib import admin
from .models import Author, Publisher, Category, Book, BookCopy, DigitalResource, BookReview

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'country')
    search_fields = ('author_name', 'biography')

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('publisher_name', 'email', 'phone')
    search_fields = ('publisher_name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name',)
    search_fields = ('category_name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'isbn', 'author', 'category', 'available_copies', 'publication_year')
    list_filter = ('category', 'language', 'publication_year')
    search_fields = ('title', 'isbn', 'author__author_name')
    readonly_fields = ('available_copies', 'average_rating')

@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'book', 'status')
    list_filter = ('status',)
    search_fields = ('barcode', 'book__title')

@admin.register(DigitalResource)
class DigitalResourceAdmin(admin.ModelAdmin):
    list_display = ('book', 'file_type', 'access_level', 'download_count', 'uploaded_at')
    list_filter = ('access_level', 'file_type')
    search_fields = ('book__title',)

@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('book__title', 'user__username', 'comment')