from django.urls import path

from . import views

urlpatterns = [
    path('leave', views.Leave_Request.as_view(), name="leave"),
    path('leave/detail/<str:pk>', views.LeaveDetail.as_view(), name='LeaveDetail'),
    path('LeaveApprove/<str:pk>', views.LeaveApproval.as_view(), name='LeaveApprove'),
    path('LeaveCancel/<str:pk>', views.LeaveCancelApproval.as_view(), name='LeaveCancel'),
    path('FnGenerateLeave/<str:pk>', views.FnGenerateLeaveReport.as_view(),name='FnGenerateLeaveReport'),
    path("DeleteLeaveAttachment/<str:pk>",views.DeleteLeaveAttachment.as_view(),name ="DeleteLeaveAttachment"),
    path("FnLeaveBalances",views.FnLeaveBalances.as_view(),name ="FnLeaveBalances"),


    path('training', views.Training_Request.as_view(), name='training_request'),
    path('training/detail/<str:pk>', views.TrainingDetail.as_view(), name='TrainingDetail'),
    path('TrainApprove/<str:pk>', views.TrainingApproval.as_view(), name='TrainApprove'),
    path('TrainCancel/<str:pk>', views.TrainingCancelApproval.as_view(), name='TrainCancel'),
    path('FnGenerateTraining/<str:pk>', views.FnGenerateTrainingReport.as_view(),name='FnGenerateTrainingReport'),
    path('UploadTrainingAttachment/<str:pk>', views.UploadTrainingAttachment.as_view(),name='UploadTrainingAttachment'),

    path('FnAdhocLineDelete/<str:pk>',views.FnAdhocLineDelete.as_view(), name='FnAdhocLineDelete'),
    path('PayrollDocuments', views.PayrollDocuments.as_view(), name='PayrollDocuments'),
    
    path('disciplinary',views.Disciplinary,name="disciplinary"),
    path('DisciplineDetails/<str:pk>', views.DisciplineDetail,name='DisciplineDetail'),
    path('DisciplineResponse/<str:pk>', views.DisciplinaryResponse,name='DisciplineResponse'),
]
