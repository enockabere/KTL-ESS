from django.urls import path
from . import views

urlpatterns = [
    path('PurchaseRequisition', views.PurchaseRequisition.as_view(), name='purchase'),
    path('PurchaseDetail/<str:pk>', views.PurchaseRequestDetails.as_view(), name='PurchaseDetail'),
    path('PurchaseApprove/<str:pk>', views.PurchaseApproval.as_view(), name='PurchaseApprove'),
    path('PurchaseCancel/<str:pk>', views.FnCancelPurchaseApproval.as_view(), name='PurchaseCancel'),
    path('FnDeletePurchaseRequisitionLine/<str:pk>',views.FnDeletePurchaseRequisitionLine.as_view(), name='FnDeletePurchaseRequisitionLine'),
    path('FnGeneratePurchaseReport/<str:pk>',views.FnGeneratePurchaseReport.as_view(), name='FnGeneratePurchaseReport'),
    path('UploadPurchaseAttachment/<str:pk>',views.UploadPurchaseAttachment.as_view(), name='UploadPurchaseAttachment'),
    path('DeletePurchaseAttachment/<str:pk>', views.DeletePurchaseAttachment.as_view(), name='DeletePurchaseAttachment'),
    path('RequisitionCategory',views.RequisitionCategory, name='RequisitionCategory'),

    path('RepairRequest', views.RepairRequest.as_view(), name='repair'),
    path('RepairDetail/<str:pk>', views.RepairRequestDetails.as_view(), name='RepairDetail'),
    path('RepairApprove/<str:pk>', views.RepairApproval, name='RepairApprove'),
    path('RepairCancel/<str:pk>', views.FnCancelRepairApproval, name='RepairCancel'),
    path('FnDeleteRepair/<str:pk>',views.FnDeleteRepairRequisitionLine, name='FnDeleteRepairRequisitionLine'),
    path('DeleteRepairAttachment/<str:pk>',views.DeleteRepairAttachment, name='DeleteRepairAttachment'),
    path('FnGenerateRepairReport/<str:pk>',views.FnGenerateRepairReport, name='FnGenerateRepairReport'),



    path('StoreRequest', views.StoreRequest.as_view(), name='store'),
    path('StoreDetail/<str:pk>',views.StoreRequestDetails.as_view(), name='StoreDetail'),
    path('StoreApprove/<str:pk>', views.StoreApproval, name='StoreApprove'),
    path('StoreCancel/<str:pk>',views.FnCancelStoreApproval, name='StoreCancel'),
    path('FnDeleteStore/<str:pk>', views.FnDeleteStoreRequisitionLine, name='FnDeleteStoreRequisitionLine'),
    path('FnGenerateStoreReport/<str:pk>',views.FnGenerateStoreReport, name='FnGenerateStoreReport'),
    path('UploadStoreAttachment/<str:pk>',views.UploadStoreAttachment.as_view(), name='UploadStoreAttachment'),
    path('itemCategory', views.itemCategory, name='itemCategory'),
    path('DeleteStoreAttachment/<str:pk>',views.DeleteStoreAttachment.as_view(), name='DeleteStoreAttachment'),
    path('itemUnitOfMeasure',views.itemUnitOfMeasure, name='itemUnitOfMeasure'),
    path('general',views.GeneralRequisition.as_view(), name='GeneralRequisition'),
    path('GeneralRequisitionDetails/<str:pk>',views.GeneralRequisitionDetails.as_view(), name='GeneralRequisitionDetails'),
    path('FnDeleteGeneralRequisitionLine/<str:pk>',views.FnDeleteGeneralRequisitionLine, name='FnDeleteGeneralRequisitionLine'),
    path('UploadGeneralAttachment/<str:pk>',views.UploadGeneralAttachment, name='UploadGeneralAttachment'),
    path('DeleteGeneralAttachment/<str:pk>',views.DeleteGeneralAttachment, name='DeleteGeneralAttachment'),
    path('GeneralApproval/<str:pk>',views.GeneralApproval, name='GeneralApproval'),
    path('FnCancelGeneralApproval/<str:pk>',views.FnCancelGeneralApproval, name='FnCancelGeneralApproval'),
    path('FnGenerateGeneralReport/<str:pk>',views.FnGenerateGeneralReport, name='FnGenerateGeneralReport'),
]
