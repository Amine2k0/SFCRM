from django.shortcuts import render, redirect,get_object_or_404,HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from .models import Ticket,Agent,Client
from .forms import AddTicketform,EditTicketform,RegisterForm,LoginForm
from django.contrib.admin.views.decorators import staff_member_required
# Create your views here.



def login_user(request):
    if request.method == "POST":
        form=LoginForm(request.POST)
        if form.is_valid():
            username=form.cleaned_data['username']
            password=form.cleaned_data['password']
            user=authenticate(request,username=username,password=password)
            if user is not None:
                login(request,user)
                if user.is_superuser:
                    return redirect('home')
                return redirect('ticket')
            else:
                return render(request,'login.html',{'form':form,'error_message':'Invalid Login'})
    else:
        form=LoginForm()
    return render(request,'login.html',{'form':form})
    
def logout_user(request):
    logout(request)
    messages.success(request, ("You were logged out."))
    return redirect("login")

def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("Registration successful."))
            return redirect("ticket")
    else:
        form = RegisterForm()

    return render(request, 'register.html', {
        'form':form,
    })


@login_required
def home(request):
    if request.user.is_superuser:
        with connection.cursor() as cursor:

            query1 = """
            SELECT count(*)/(SELECT COUNT(*) FROM `crm_ticket`)*100
            FROM `crm_ticket`
            WHERE Status='Closed';
            """
            query2 ="""SELECT count(*)
            FROM crm_ticket
            WHERE Agent_id is not null and Date > '2024-5-8 00:00:00' ;
            """
            query3 ="""SELECT count(*)
            FROM crm_ticket
            WHERE Status='Closed' ;
            """
            query4 ="""SELECT count(*)
            FROM crm_ticket
            WHERE Status='Open' ;
            """
            query5 ="""SELECT count(*)
            FROM crm_ticket
            WHERE Status='Solved' ;
            """
            query6 ="""SELECT count(*)
            FROM crm_ticket
            WHERE Status='Pending' ;
            """
            cursor.execute(query1)
            completed =round(cursor.fetchone()[0],1)
            cursor.execute(query2)
            assigned = cursor.fetchone()[0]
            cursor.execute(query3)
            Closed = cursor.fetchone()[0]
            cursor.execute(query4)
            Open = cursor.fetchone()[0]
            cursor.execute(query5)
            Solved = cursor.fetchone()[0]
            cursor.execute(query6)
            Pending = cursor.fetchone()[0]
    
        context = {
            'closed_ticket_percentage': completed,
            'assigned_ticket_percentage': assigned,
            'closed':Closed,
            'open':Open,
            'solved':Solved,
            'pending':Pending,
        }
        return render(request,"home.html",context)  
            
    else:
        
        return HttpResponse('You dont have permission')
    

@login_required
def ticket(request):
    if request.user.is_superuser:
        Tickets=Ticket.objects.all()
    elif request.user.is_staff:
        Tickets=Ticket.objects.filter(Agent=request.user.id)
    else:
        Tickets=Ticket.objects.filter(Client=request.user.id)
    context={'Tickets':Tickets}
    return render(request,"ticket.html",context)



@login_required
def user(request):
    if request.user.is_superuser:   
        agents=Agent.objects.all()
        clients=Client.objects.all()
        context={'Agents':agents,'Clients':clients}
        return render(request,"user.html",context)
    else:
        return HttpResponse('You dont have permission')
    

@login_required
def AddTicket(request):
    agent=Agent.objects.filter(Dispo=True)
    client=Client.objects.get(id=request.user.id)
    if request.method == 'POST':
        form = AddTicketform(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.Client = client
            ticket.Agent = agent[0]
            ticket.Status = 'Open'
            ticket.save()
            return redirect('ticket')
        else:
            print(form.errors.as_data())
    else:
        form = AddTicketform()
    return render(request,'addticket.html', {'form': form})

@staff_member_required
@login_required
def EditTicket(request,id):
      
    instance = get_object_or_404(Ticket, pk=id)
    
    if request.method == 'POST':
        form = EditTicketform(request.POST,instance=instance)  
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.Client=instance.Client  
            ticket.Agent=instance.Agent
            ticket.save()
            return redirect('ticket')
    else:
        form = EditTicketform(instance=instance) 
        
    context = {'form': form, 'ticket': instance} 
    return render(request, 'editticket.html',context)

@staff_member_required
@login_required
def DeleteTicket(request,id):
    instance = get_object_or_404(Ticket, pk=id)
    
    instance.delete()
    return redirect('ticket')
    
    



