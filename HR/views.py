import asyncio
import base64
import logging
import aiohttp
from django.shortcuts import render, redirect
from datetime import datetime
import requests
import json
from django.conf import settings as config
import datetime as dt
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
import io as BytesIO
import secrets
import string
from django.views import View
from myRequest.views import UserObjectMixins
from asgiref.sync import sync_to_async
# Create your views here.
class Leave_Request(UserObjectMixins,View):
    async def get(self,request):
        try:
            UserId = await sync_to_async(request.session.__getitem__)('User_ID')
            full_name = await sync_to_async(request.session.__getitem__)('full_name')
            department = await sync_to_async(request.session.__getitem__)('User_Responsibility_Center')
            openLeave = []
            approvedLeave = []
            Leave = []
            pendingLeave = []
            relievers = []
                        
            async with aiohttp.ClientSession() as session:
                task_get_leave = asyncio.ensure_future(self.fetch_one_filtered_data(session,
                                         "/QyLeaveApplications","User_ID","eq",UserId))
                task_get_leave_types = asyncio.ensure_future(self.simple_fetch_data(session,
                                                                      "/QyLeaveTypes"))
                task_get_reliever = asyncio.ensure_future(self.simple_double_filtered_data(session,
                                            "/QyEmployees","Global_Dimension_2_Code","eq",department,
                                            "and","User_ID", "ne",UserId))
                response = await asyncio.gather(task_get_leave,task_get_leave_types,task_get_reliever)

                openLeave = [x for x in response[0]['data'] if x['Status'] == 'Open']
                pendingLeave = [x for x in response[0]['data'] if x['Status'] == 'Pending Approval']
                approvedLeave = [x for x in response[0]['data'] if x['Status'] == 'Released']
                Leave = [x for x in response[1]]
                relievers = [x for x in response[2] if x['Global_Dimension_2_Code'] ==department]
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except requests.exceptions.ConnectionError as e:
            print(e)
        
        ctx = {
            "today": self.todays_date, "res": openLeave,
            "response": approvedLeave,'leave': Leave,
            "pending": pendingLeave,
            "full": full_name,"relievers":relievers,
            }
        return render(request, 'leave.html', ctx)
        
    async def post(self, request):
        try:
            soap_headers = await sync_to_async(request.session.__getitem__)('soap_headers')
            applicationNo = request.POST.get('applicationNo')
            employeeNo = await sync_to_async(request.session.__getitem__)('Employee_No_')
            usersId = await sync_to_async(request.session.__getitem__)('User_ID')
            leaveType = request.POST.get('leaveType')
            plannerStartDate = datetime.strptime(request.POST.get('plannerStartDate'), '%Y-%m-%d').date()
            daysApplied = int(request.POST.get('daysApplied'))
            isReturnSameDay = eval(request.POST.get('isReturnSameDay'))
            myAction = request.POST.get('myAction')
            reliever = request.POST.get('reliever')
            if not daysApplied:
                daysApplied = 0
            
            response = self.make_soap_request(soap_headers,"FnLeaveApplication",
                    applicationNo, employeeNo, usersId, leaveType,
                     plannerStartDate, daysApplied, isReturnSameDay, myAction)
            if response !='0':
                add_reliever = self.make_soap_request(soap_headers,"FnLeaveReliever",
                                                      response,reliever)
                print("reliever response:",add_reliever)
                if add_reliever !='0':
                    messages.success(request, "Success")
                    return redirect('LeaveDetail', pk=add_reliever)
                if add_reliever == '0':
                    messages.info(request, f"Leave reliever not added.")
                    return redirect('LeaveDetail', pk=response)
            if response == '0':
                messages.error(request, response)
                return redirect('leave')
        except Exception as e:
            messages.error(request, f"{e}")
            print(e)
            return redirect('leave')
class FnLeaveBalances(UserObjectMixins,View):
    def post(self,request):
        try:
            soap_headers = request.session['soap_headers']
            Employee_No_ = request.session['Employee_No_']
            
            response = self.make_soap_request(soap_headers,
                            "FnLeaveBalances",Employee_No_)
            if response.isnumeric():
                return JsonResponse(response,safe=False)
            else:
                return JsonResponse(0,safe=False)
        except Exception as e:
            print(e)
            return JsonResponse(0,safe=False)
class LeaveDetail(UserObjectMixins,View):
    def get(self,request,pk):
        try:
            userId = request.session['User_ID']
            full_name =request.session['full_name']

            response = self.double_filtered_data("/QyLeaveApplications","Application_No","eq",pk,
                                        "and","User_ID","eq",userId)
            for leave in response[1]:
                res=leave

            res_approver = self.one_filter("/QyApprovalEntries","Document_No_","eq",pk)
            Approvers = [x for x in res_approver[1]]

            res_file = self.one_filter("/QyDocumentAttachments","No_","eq",pk)
            allFiles = [x for x in res_file[1]]

            RejectedResponse = self.one_filter("/QyApprovalCommentLines","Document_No_","eq",pk)
            Comments = [x for x in RejectedResponse[1]]
        except KeyError:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except requests.exceptions.ConnectionError as e:
                print(e)
                messages.error(request,"500 Server Error, Try Again")
                return redirect('leave')

        ctx = {
            "today": self.todays_date, "res": res,
            "Approvers": Approvers,"full": full_name,"file":allFiles,"Comments":Comments
            }
        return render(request, 'leaveDetail.html', ctx)

    def post(self,request,pk):
        try:
            soap_headers = request.session['soap_headers']
            attachments = request.FILES.getlist('attachment')
            tableID = 52177494
            attachment_names = []
            response = False
            for file in attachments:
                fileName = file.name
                attachment_names.append(fileName)
                attachment = base64.b64encode(file.read())
                response = self.upload_attachment(soap_headers,pk, fileName, attachment,
                                                  tableID, request.session['User_ID']) 
            if response is not None:
                if response == True:
                    messages.success(request, "Uploaded {} attachments successfully".format(len(attachments)))
                    return redirect('LeaveDetail', pk=pk)
                messages.error(request, "Upload failed: {}".format(response))
                return redirect('LeaveDetail', pk=pk)
            messages.error(request, "Upload failed: Response from server was None")
            return redirect('LeaveDetail', pk=pk)
        except Exception as e:
            messages.error(request, "Upload failed: {}".format(e))
            logging.exception(e)
            return redirect('LeaveDetail', pk=pk)
   
    
class DeleteLeaveAttachment(UserObjectMixins,View):
    def post(self,request,pk):
        if request.method == "POST":
            try:
                soap_headers = request.session['soap_headers']
                docID = int(request.POST.get('docID'))
                tableID= int(request.POST.get('tableID'))
                response = self.delete_attachment(soap_headers,
                    pk,docID,tableID)
                if response == True:
                    messages.success(request, "Deleted Successfully")
                    return redirect('LeaveDetail', pk=pk)
                messages.error(request, response)
                
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('LeaveDetail', pk=pk)

class LeaveApproval(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                soap_headers = request.session['soap_headers']
                employeeNo = request.session['Employee_No_']
                applicationNo = request.POST.get('applicationNo')

                response = self.make_soap_request(soap_headers,'FnRequestLeaveApproval',
                        employeeNo, applicationNo)
                if response == True:
                    messages.success(request, "Request Successful")
                    return redirect('LeaveDetail', pk=pk)
                messages.error(request, response)
                return redirect('LeaveDetail', pk=pk)
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('LeaveDetail', pk=pk)


class LeaveCancelApproval(UserObjectMixins, View):
    def post(self,request,pk):
        try:
            if request.method == 'POST':
                employeeNo = request.session['Employee_No_']
                soap_headers = request.session['soap_headers']
                applicationNo = request.POST.get('applicationNo')

            response = self.make_soap_request(soap_headers,'FnCancelLeaveApproval',
                    employeeNo, applicationNo)
            if response == True:
                messages.success(request, "Success")
                return redirect('LeaveDetail', pk=pk)
            messages.error(request, response)
            return redirect('LeaveDetail', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('LeaveDetail', pk=pk)


class Training_Request(UserObjectMixins,View):
    async def get(self, request):
        try:
            full_name = await sync_to_async(request.session.__getitem__)('full_name')
            empNo = await sync_to_async(request.session.__getitem__)('Employee_No_')
            
            async with aiohttp.ClientSession() as session:
                get_trainings_task = asyncio.ensure_future(self.fetch_one_filtered_data(session,
                                        "/QyTrainingRequests","Employee_No","eq",empNo))
                task_get_training_needs = asyncio.ensure_future(self.simple_fetch_data(session,
                                                                            '/QyTrainingNeeds'))
                response = await asyncio.gather(get_trainings_task,task_get_training_needs)
                
                openTraining = [x for x in response[0]['data'] if x['Status'] == 'Open']
                pendingTraining = [x for x in response[0]['data'] if x['Status'] == 'Pending Approval']
                approvedTraining = [x for x in response[0]['data'] if x['Status'] == 'Released']
                trains = [x for x in response[1]]

        except KeyError as e:
            print(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            messages.error(request, "Server failed")
            logging.exception(e)
            return redirect('dashboard')

        ctx = {
            "today": self.todays_date, "res": openTraining,
            "response": approvedTraining,
            "train": trains,"pending": pendingTraining,
            "full": full_name
            }
        return render(request, 'training.html', ctx)
    async def post(self,request):
        try:
            soap_headers = await sync_to_async(request.session.__getitem__)('soap_headers')
            employeeNo = await sync_to_async(request.session.__getitem__)('Employee_No_')
            usersId = await sync_to_async(request.session.__getitem__)('User_ID')
            requestNo = request.POST.get('requestNo')
            isAdhoc = eval(request.POST.get('isAdhoc'))
            trainingNeed = request.POST.get('trainingNeed')
            myAction = request.POST.get('myAction')

            if not trainingNeed:
                trainingNeed = 'none'

            response = self.make_soap_request(soap_headers,'FnTrainingRequest',
                requestNo, employeeNo, usersId, isAdhoc, trainingNeed, myAction)
            if response != '0':
                messages.success(request, "Success")
                return redirect('TrainingDetail', pk=response)
            if response == '0':
                messages.error(request, response)
                return redirect('training_request')
        except Exception as e:
            messages.error(request, 'Failed, non-201 error')
            logging.exception(e)
            return redirect('training_request')


class TrainingDetail(UserObjectMixins, View):
    async def get(self,request,pk):
        try:
            employeeNo = await sync_to_async(request.session.__getitem__)('Employee_No_')
            full_name = await sync_to_async(request.session.__getitem__)('full_name')
            res = {}
            Approvers = []
            Local = []
            Foreign = []
            Comments = []
            openLines =[]
            
            async with aiohttp.ClientSession() as session:
                task_get_training = asyncio.ensure_future(self.simple_double_filtered_data(session,
                                            "/QyTrainingRequests","Request_No_","eq",pk,"and","Employee_No",
                                            "eq",employeeNo))
                task_get_approvers = asyncio.ensure_future(self.simple_one_filtered_data(session,
                                                "/QyApprovalEntries","Document_No_","eq",pk))
                task_get_destinations = asyncio.ensure_future(self.simple_fetch_data(session,
                                                                            '/QyDestinations'))
                task_get_approval_comments = asyncio.ensure_future(self.simple_one_filtered_data(session,
                                                        "/QyApprovalCommentLines","Document_No_","eq",pk))
                task_get_training_lines = asyncio.ensure_future(self.simple_double_filtered_data(session,
                                                    "/QyTrainingNeedsRequest","Source_Document_No","eq",pk,
                                                                            "and","Employee_No","eq",employeeNo))
                task_get_attachments = asyncio.ensure_future(self.simple_one_filtered_data(session,
                                                                            "/QyDocumentAttachments","No_","eq",pk))
                response = await asyncio.gather(task_get_training,task_get_approvers,task_get_destinations,
                                                task_get_approval_comments,task_get_training_lines,
                                                task_get_attachments)

                for training in response[0]:
                    res = training
                Approvers = [x for x in response[1]]
                
                Local = [x for x in response[2] if x['Destination_Type'] == 'Local']
                Foreign = [x for x in response[2] if x['Destination_Type'] == 'Foreign']
                Comments = [x for x in response[3]]
                openLines = [x for x in response[4]]
                allFiles = [x for x in response[5]]
        except KeyError as e:
            logging.exception(e)
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            messages.error(request, 'Failed, non-200 error')
            logging.exception(e)
            return redirect('training_request')

        ctx = {
            "today": self.todays_date, "res": res,
            "Approvers": Approvers, "full": full_name,"file":allFiles,
            "line": openLines,"local":Local,"foreign":Foreign,"Comments":Comments
            }
        return render(request, 'trainingDetail.html', ctx)
    async def post(self,request,pk):
        try:
            soap_headers = await sync_to_async(request.session.__getitem__)('soap_headers')
            employeeNo = await sync_to_async(request.session.__getitem__)('Employee_No_')
            requestNo = pk
            no = ""
            employeeNo = request.session['Employee_No_']
            trainingName = request.POST.get('trainingName')
            trainingArea = request.POST.get('trainingArea')
            trainingObjectives = request.POST.get('trainingObjectives')
            venue = request.POST.get('venue')
            provider = request.POST.get('provider')
            myAction = request.POST.get('myAction')
            startDate = datetime.strptime((request.POST.get('startDate')), '%Y-%m-%d').date()
            endDate = datetime.strptime((request.POST.get('endDate')), '%Y-%m-%d').date()
            destination = request.POST.get('destination')
            OtherDestinationName = request.POST.get('OtherDestinationName')
            trainingCost = float(request.POST.get('trainingCost'))

            if not destination:
                destination = 'none'
            
            if not venue:
                venue = "Online"

            if OtherDestinationName:
                destination = OtherDestinationName
            if not trainingCost:
                trainingCost = 0
  
            response = self.make_soap_request(soap_headers,'FnAdhocTrainingNeedRequest',
                requestNo,no, employeeNo, trainingName, trainingArea, trainingObjectives,
                    venue, provider, myAction,startDate,endDate,destination,trainingCost)
            if response == True:
                messages.success(request, "Success")
                return redirect('TrainingDetail', pk=pk)
            if response == False:
                messages.error(request, "Failed, non-201 error")
                return redirect('TrainingDetail', pk=pk)
        except Exception as e:
            messages.error(request, 'Failed, non-201 error')
            logging.exception(e)
            return redirect('TrainingDetail', pk=pk)
class UploadTrainingAttachment(UserObjectMixins, View):
    def post(self,request,pk):
        try:
            attachments = request.FILES.getlist('attachment')
            soap_headers = request.session['soap_headers']
            tableID = 52177501
            attachment_names = []
            response = False

            for file in attachments:
                fileName = file.name
                attachment_names.append(fileName)
                attachment = base64.b64encode(file.read())

                response = self.upload_attachment(soap_headers,pk, fileName,
                                                  attachment, tableID, request.session['User_ID'])
            if response is not None:
                if response == True:
                    messages.success(request, "Uploaded {} attachments successfully".format(len(attachments)))
                    return redirect('TrainingDetail', pk=pk)
                messages.error(request, "Upload failed: {}".format(response))
                return redirect('TrainingDetail', pk=pk)
            messages.error(request, "Upload failed: Response from server was None")
            return redirect('TrainingDetail', pk=pk)
        except Exception as e:
            messages.error(request, "Upload failed: {}".format(e))
            logging.exception(e)
            return redirect('TrainingDetail', pk=pk)

class FnAdhocLineDelete(UserObjectMixins, View):
    def post(self,request,pk):
        try:
            requestNo = pk
            soap_headers = request.session['soap_headers']
            needNo = request.POST.get('needNo')

            response = self.make_soap_request(soap_headers, 'FnDeleteAdhocTrainingNeedRequest',
                needNo,requestNo)
            if response == True:
                messages.success(request, "Successfully Deleted")
                return redirect('TrainingDetail', pk=pk)
            messages.success(request, response)
            return redirect('TrainingDetail', pk=pk)
        except Exception as e:
            messages.error(request, e)
            print(e)
            return redirect('TrainingDetail', pk=pk)


class TrainingApproval(UserObjectMixins, View):
    async def post(self,request,pk):
        try:
            soap_headers = await sync_to_async(request.session.__getitem__)('soap_headers')
            myUserID = await sync_to_async(request.session.__getitem__)('User_ID')
            trainingNo = request.POST.get('trainingNo')

            response = self.make_soap_request(soap_headers,'FnRequestTrainingApproval',
                myUserID, trainingNo)
            if response == True:
                messages.success(request, "Approval Request Successfully Sent")
                return redirect('TrainingDetail', pk=pk)
            if response == False:
                messages.error(request, 'Failed, non-201 error')
                return redirect('TrainingDetail', pk=pk)
        except Exception as e:
            messages.error(request, 'Failed, server error')
            logging.exception(e)
            return redirect('TrainingDetail', pk=pk)


class TrainingCancelApproval(UserObjectMixins, View):
    async def post(self,request,pk):
        try:
            soap_headers = await sync_to_async(request.session.__getitem__)('soap_headers')
            myUserID = await sync_to_async(request.session.__getitem__)('User_ID')
            trainingNo = request.POST.get('trainingNo')

            response = self.make_soap_request(soap_headers,'FnCancelTrainingApproval',
            myUserID, trainingNo)
            if response == True:
                messages.success(request, "Cancel Request Successful")
                return redirect('TrainingDetail', pk=pk)
            if response == False:
                messages.error(request, 'Failed, non-201 error')
                return redirect('TrainingDetail', pk=pk)
        except Exception as e:
            messages.error(request, 'Failed, server error')
            logging.exception(e)
            return redirect('TrainingDetail', pk=pk)

class PayrollDocuments(UserObjectMixins,View):
    async def get(self,request):
        try:
            full_name = await sync_to_async(request.session.__getitem__)('full_name')
            res = []
            
            async with aiohttp.ClientSession() as session:
                task_get_closed_payroll_period = asyncio.ensure_future(self.simple_fetch_data(session,
                            '/QyPayrollPeriods?$filter=Closed%20eq%20true%20and%20Status%20eq%20%27Approved%27')) 
                response = await asyncio.gather(task_get_closed_payroll_period)          
                res = [x for x in response[0]]
        except KeyError as e:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            messages.error(request, 'Failed, non-200 error')
            logging.exception(e)
            return redirect('pNine')
        ctx = {
            "today": self.todays_date,
            "full": full_name,
            "res":res
            }
        return render(request, "payroll_docs.html", ctx)
    
    async def post(self,request):
        try:
            soap_headers = await sync_to_async(request.session.__getitem__)('soap_headers')
            employeeNo = await sync_to_async(request.session.__getitem__)('Employee_No_')
            startDate = request.POST.get('startDate')
            document_type =int(request.POST.get('document_type'))

            if document_type == 1:
                paymentPeriod = datetime.strptime(startDate, '%Y-%m-%d').date()
                filenameFromApp = f"P9_For_{paymentPeriod}.pdf"
                response = self.make_soap_request(soap_headers,'FnGeneratePayslip',
                    employeeNo, filenameFromApp, paymentPeriod)
            elif document_type == 2:
                year = int(startDate[0:4])
                filenameFromApp = f"P9_For_{year}.pdf"
                response = self.make_soap_request(soap_headers,'FnGeneratePNine',
                    employeeNo, filenameFromApp,year)
            content = base64.b64decode(response)
            response = HttpResponse(content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment;filename={filenameFromApp}'
            return response
        except KeyError as e:
            messages.info(request, "Session Expired. Please Login")
            return redirect('auth')
        except Exception as e:
            messages.error(request, 'Failed, non-200 error')
            logging.exception(e)
            return redirect('PayrollDocuments')

class FnGenerateLeaveReport(UserObjectMixins, View):
    def post(self,request,pk):    
        if request.method == 'POST':
            try:
                employeeNo = request.session['Employee_No_']
                nameChars = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                            for i in range(5))
                filenameFromApp = pk + str(nameChars) + ".pdf"

                response = self.zeep_client(request).service.FnGenerateLeaveReport(
                    employeeNo, filenameFromApp, pk)
                buffer = BytesIO.BytesIO()
                content = base64.b64decode(response)
                buffer.write(content)
                responses = HttpResponse(
                    buffer.getvalue(),
                    content_type="application/pdf",
                )
                responses['Content-Disposition'] = f'inline;filename={filenameFromApp}'
                return responses
            except Exception as e:
                messages.error(request, e)
                print(e)
        return redirect('LeaveDetail', pk=pk)

class FnGenerateTrainingReport(UserObjectMixins, View):
    def post(self,request,pk):
        if request.method == 'POST':
            try:
                nameChars = ''.join(secrets.choice(string.ascii_uppercase + string.digits)
                            for i in range(5))
                employeeNo = request.session['Employee_No_']

                filenameFromApp = pk + str(nameChars) + ".pdf"
                response = self.zeep_client(request).service.FnGenerateTrainingReport(
                    employeeNo, filenameFromApp, pk)
                buffer = BytesIO.BytesIO()
                content = base64.b64decode(response)
                buffer.write(content)
                responses = HttpResponse(
                    buffer.getvalue(),
                    content_type="application/pdf",
                )
                responses['Content-Disposition'] = f'inline;filename={filenameFromApp}'
                return responses
            except Exception as e:
                messages.error(request, e)
                print(e)
            return redirect('TrainingDetail', pk=pk)

def Disciplinary(request):
    fullname = request.session['User_ID']
    session = requests.Session()
    session.auth = config.AUTHS

    Access_Point = config.O_DATA.format("/QyEmployeeDisciplinaryCases")
    try:
        response = session.get(Access_Point, timeout=10).json()
        openCase = []
        for case in response['value']:
            if case['Employee_No'] == request.session['Employee_No_'] and case['Posted'] == False and case['Sent_to_employee'] == True and case['Submit'] == False:
                output_json = json.dumps(case)
                openCase.append(json.loads(output_json))
        counts = len(openCase)
        print(counts)
    except requests.exceptions.ConnectionError as e:
        print(e)

    todays_date = dt.datetime.now().strftime("%b. %d, %Y %A")
    ctx = {"today": todays_date, "res": openCase,
           "full": fullname,
           "count": counts}
    return render(request,'disciplinary.html',ctx)

def DisciplineDetail(request,pk):
    fullname = request.session['User_ID']
    session = requests.Session()
    session.auth = config.AUTHS
    res = ''
    Access_Point = config.O_DATA.format("/QyEmployeeDisciplinaryCases")
    try:
        response = session.get(Access_Point, timeout=10).json()
        Case = []
        for case in response['value']:
            if case['Employee_No'] == request.session['Employee_No_'] and case['Posted'] == False and case['Sent_to_employee'] == True and case['Submit'] == False:
                output_json = json.dumps(case)
                Case.append(json.loads(output_json))
                for case in Case:
                    if case['Disciplinary_Nos'] == pk:
                        res = case
    except requests.exceptions.ConnectionError as e:
        print(e)
    Lines_Res = config.O_DATA.format("/QyEmployeeDisciplinaryLines")
    try:
        responses = session.get(Lines_Res, timeout=10).json()
        openLines = []
        for cases in responses['value']:
            if cases['Refference_No'] == pk and cases['Employee_No'] == request.session['Employee_No_']:
                output_json = json.dumps(cases)
                openLines.append(json.loads(output_json))
    except requests.exceptions.ConnectionError as e:
        print(e)
    todays_date = dt.datetime.now().strftime("%b. %d, %Y %A")
    ctx = {"today": todays_date, "res": res, "full": fullname,"line": openLines}
    return render (request, 'disciplineDetail.html',ctx)

def DisciplinaryResponse(request, pk):

    employeeNo = request.session['Employee_No_']
    caseNo = pk
    myResponse = ''
    
    if request.method == 'POST':
        try:
            myResponse = request.POST.get('myResponse')
        except ValueError as e:
            messages.error(request, "Invalid, Try Again!!")
            return redirect('DisciplineDetail', pk=pk)
    try:
        response = config.CLIENT.service.FnEmployeeDisciplinaryResponse(
            employeeNo, caseNo, myResponse)
        messages.success(request, "Response Successful Sent!!")
        print(response)
        return redirect('DisciplineDetail', pk=pk)
    except Exception as e:
        messages.error(request, e)
        print(e)
    return redirect('DisciplineDetail', pk=pk)

