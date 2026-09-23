from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('<int:book_id>/', views.book_detail, name='book_detail'),
    
    # Phase 6 - Book Management
    path('manage/', views.manage_books, name='manage_books'),
    path('add/', views.add_book, name='add_book'),
    path('<int:book_id>/edit/', views.edit_book, name='edit_book'),
    path('<int:book_id>/delete/', views.delete_book, name='delete_book'),
    # Authors
path('authors/', views.manage_authors, name='manage_authors'),
path('authors/add/', views.add_author, name='add_author'),
path('authors/<int:author_id>/edit/', views.edit_author, name='edit_author'),
path('authors/<int:author_id>/delete/', views.delete_author, name='delete_author'),

# Categories
path('categories/', views.manage_categories, name='manage_categories'),
path('categories/add/', views.add_category, name='add_category'),
path('categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),

# Publishers
path('publishers/', views.manage_publishers, name='manage_publishers'),
path('publishers/add/', views.add_publisher, name='add_publisher'),
path('publishers/<int:publisher_id>/edit/', views.edit_publisher, name='edit_publisher'),
path('publishers/<int:publisher_id>/delete/', views.delete_publisher, name='delete_publisher'),

# Digital Resources
path('<int:book_id>/digital/', views.manage_digital_resources, name='manage_digital'),
path('<int:book_id>/digital/upload/', views.upload_digital_resource, name='upload_digital'),
path('digital/<int:resource_id>/delete/', views.delete_digital_resource, name='delete_digital'),
path('digital/<int:resource_id>/download/', views.download_digital_resource, name='download_digital'),

# Reviews
path('<int:book_id>/review/', views.add_review, name='add_review'),
path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),

path('live-search/', views.live_search_books, name='live_search'),
]  