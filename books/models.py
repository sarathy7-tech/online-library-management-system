from django.db import models

# Create your models here.
from django.db import models

class Author(models.Model):
    author_name = models.CharField(max_length=150)
    biography = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.author_name

class Publisher(models.Model):
    publisher_name = models.CharField(max_length=150)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.publisher_name

class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.category_name

class Book(models.Model):
    title = models.CharField(max_length=255)
    isbn = models.CharField(max_length=30, unique=True, blank=True, null=True)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True, related_name='books')
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    publication_year = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=50, default='English')
    edition = models.CharField(max_length=50, blank=True)
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    shelf_location = models.CharField(max_length=50, blank=True)
    summary = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_digital = models.BooleanField(default=False)
    keywords = models.TextField(blank=True)  # for search
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']

class BookCopy(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    barcode = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Available', 'Available'),
            ('Issued', 'Issued'),
            ('Reserved', 'Reserved'),
            ('Lost', 'Lost'),
            ('Damaged', 'Damaged')
        ],
        default='Available'
    )

    def __str__(self):
        return f"{self.book.title} - {self.barcode}"    
    
# ... your existing models (BookCopy etc.) ...

class DigitalResource(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='digital_resources')
    file = models.FileField(upload_to='digital_books/')
    file_type = models.CharField(max_length=50, blank=True)
    access_level = models.CharField(
        max_length=20, 
        default='Member', 
        choices=[('Public', 'Public'), ('Member', 'Member')]
    )
    download_count = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Digital: {self.book.title}"


class BookReview(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('book', 'user')

    def __str__(self):
        return f"Review by {self.user} on {self.book}"