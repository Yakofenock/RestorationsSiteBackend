from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter


# All abilities encapsulated:
router = DefaultRouter()
router.register('restorations', RestorationViewSet)
router.register('works',        WorkViewSet)
router.register('payments',     PaymentViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('manage_payment_status/',                PaymentStatusUserView.as_view()),
    path('manage_payment_status_admin/<int:pk>/', PaymentStatusAdminView.as_view()),
    path('manage_payment_donation/',              PaymentDonationView.as_view()),
    path('asinc_pay_service/',                    AsincServiceMount.as_view())
]
