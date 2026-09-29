from django.urls import path
from .views import RegisterView, LoginView, CardListCreateView, CardDeleteView, TransactionListView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('cards/', CardListCreateView.as_view(), name='cards'),
    path('cards/<int:pk>/', CardDeleteView.as_view(), name='card-delete'),
    path('transactions/', TransactionListView.as_view(), name='transactions'),
]