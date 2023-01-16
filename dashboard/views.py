from django.shortcuts import render, redirect
import requests
from django.conf import settings as config
import datetime
from django.contrib import messages
from django.views import View
from myRequest.views import UserObjectMixins
# Create your views here.

class Dashboard(UserObjectMixins,View):

    def get(self,request):
        try:
            userId =  request.session['User_ID']
            empNo = request.session['Employee_No_']
            HOD_User = request.session['HOD_User']
            full_name = request.session['full_name'] 
            department_name = request.session['Department_Name'] 
            empAppraisal = ''
            pending_approval_count = 0
            
            Leave = self.one_filter("/QyLeaveApplications","User_ID","eq",userId)
            app_leave_list = len([x for x in Leave[1]  if x['Status'] == 'Released'])
            pendLeave = len([x for x in Leave[1]  if x['Status'] == 'Pending Approval'])

            Training = self.one_filter("/QyTrainingRequests","Employee_No","eq",empNo)
            app_train_list = len([x for x in Training[1]  if x['Status'] == 'Released'])
            pendTrain = len([x for x in Training[1]  if x['Status'] == 'Pending Approval'])

            myImprest = self.one_filter("/Imprests","User_Id","eq",userId)
            app_imp_list = len([x for x in myImprest[1] if x['Status'] == 'Released'])
            pending_imprest = len([x for x in myImprest[1] if x['Status'] == 'Pending Approval'])

            Surrender = self.one_filter("/QyImprestSurrenders","User_Id","eq",userId)
            app_surrender_list = len([x for x in Surrender[1]  if x['Status'] == 'Released'])
            pending_surrender = len([x for x in Surrender[1]  if x['Status'] == 'Pending Approval'])

            Claim = self.one_filter("/QyStaffClaims","User_Id","eq",userId)
            app_claim_list = len([x for x in Claim[1]  if x['Status'] == 'Released'])
            pending_claims = len([x for x in Claim[1]  if x['Status'] == 'Pending Approval'])

            Purchase = self.one_filter("/QyPurchaseRequisitionHeaders","Employee_No_","eq",empNo)
            app_purchase_list = len([x for x in Purchase[1]  if x['Status'] == 'Released'])
            pending_purchase = len([x for x in Purchase[1]  if x['Status'] == 'Pending Approval'])

            Repair = self.one_filter("/QyRepairRequisitionHeaders","Requested_By","eq",userId)
            app_repair_list = len([x for x in Repair[1] if x['Status'] == 'Released'])
            pending_repair = len([x for x in Repair[1] if x['Status'] == 'Pending Approval'])

            Store = self.one_filter("/QyStoreRequisitionHeaders","Requested_By","eq",userId)
            app_store_list = len([x for x in Store[1] if x['Status'] == 'Released'])
            pending_store = len([x for x in Store[1] if x['Status'] == 'Pending Approval'])
            
            if HOD_User == False:
                empAppraisalResponse = self.one_filter("/QyEmployeeAppraisals","EmployeeNo","eq",empNo)
                empAppraisal = len([x for x in empAppraisalResponse[1] if (x['Status']=='Self Appraisal') or (x['Status']=='Open')])

            if HOD_User == True:
                QyApprovalEntries = self.double_filtered_data("/QyApprovalEntries","Approver_ID","eq",userId,
                                                              "and","Status","eq","Open")
                pending_approval_count = QyApprovalEntries[0]
                
            payroll_url = config.O_DATA.format("/QyPayrollPeriods?$filter=Closed%20eq%20true%20and%20Status%20eq%20%27Approved%27") 
            get_payroll_periods = self.get_object(payroll_url)
            payroll_period = get_payroll_periods['value'][0]
            
            salary_advance = self.one_filter("/QySalaryAdvances","Employee_No","eq",empNo)
            Pending_advances = len([x for x in salary_advance[1] if x['Loan_Status'] == 'Being Processed'])
            approved_advances = len([x for x in salary_advance[1] if x['Loan_Status'] == 'Approved'])
            
            general_requisitions = self.one_filter("/QyGeneralRequisitionHeaders","Requested_By","eq",userId)
            pending_general = len([x for x in general_requisitions[1] if x['Status'] == 'Pending Approval'])
            approved_general = len([x for x in general_requisitions[1] if x['Status'] == 'Released'])
            
        except requests.exceptions.Timeout:
            messages.error(request, "API timeout. Server didn't respond, contact admin")
            return redirect('auth')
        except requests.exceptions.ConnectionError:
            messages.error(request, "Connection/network error,retry")
            return redirect('auth') 
        except requests.exceptions.TooManyRedirects:
            messages.error(request, "Server busy, retry")
            return redirect('auth') 
        except KeyError as e:
            print (e)
            messages.success(request, "Session Expired. Please Login")
            return redirect('auth')
        ctx = {
            "today": self.todays_date,"department_name":department_name,
            "res": open, "full": userId,"full_name":full_name,"payroll_period":payroll_period,
            "pending_imprest":pending_imprest, "imprest_app": app_imp_list,"approved_advances":approved_advances,
            "pendTrain":pendTrain,"app_train": app_train_list,"Pending_advances":Pending_advances,
            "app_store": app_store_list, "pending_store": pending_store,"pending_general":pending_general,
            "pendLeave":pendLeave, "approved_leave": app_leave_list,"approved_general":approved_general,
            "app_repair": app_repair_list,"pending_repair": pending_repair,
            "pending_surrender": pending_surrender, "surrender_app": app_surrender_list,
            "app_claim": app_claim_list,"pending_claims": pending_claims,
            "app_purchase": app_purchase_list, "pending_purchase": pending_purchase,
            "HOD_User":HOD_User,"empAppraisal":empAppraisal,"pending_approval_count":pending_approval_count,
            }
        return render(request, 'main/dashboard.html', ctx)

class Manual(View):
    def get(self, request):
        try:
            userId =  request.session['User_ID']
            todays_date = datetime.datetime.now().strftime("%b. %d, %Y %A")
        except KeyError as e:
            print (e)
            messages.success(request, "Session Expired. Please Login")
            return redirect('auth')
        ctx = {"today": todays_date,"full": userId,}
        return render(request,"manual.html",ctx)

