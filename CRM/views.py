from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AddTicketform, EditTicketform, LoginForm, RegisterForm
from .models import Agent, Client, Ticket, TicketStatus

# Number of days the dashboard counts as "recent" when reporting assigned tickets.
RECENT_WINDOW_DAYS = 30

# Tickets shown per page on the list view.
TICKETS_PER_PAGE = 10


def login_user(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_superuser:
                    return redirect("home")
                return redirect("ticket")
            else:
                return render(
                    request, "login.html", {"form": form, "error_message": "Invalid Login"}
                )
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


def logout_user(request):
    logout(request)
    messages.success(request, ("You were logged out."))
    return redirect("login")


def register_user(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, ("Registration successful."))
            return redirect("ticket")
    else:
        form = RegisterForm()

    return render(
        request,
        "register.html",
        {
            "form": form,
        },
    )


@login_required
def home(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Only administrators can view the dashboard.")

    # A single grouped query gives us the count for every status at once.
    counts = dict(
        Ticket.objects.values_list("Status")
        .annotate(total=Count("id"))
        .values_list("Status", "total")
    )
    total = sum(counts.values())
    closed = counts.get("Closed", 0)

    # Tickets routed to an agent in the last 30 days.
    recent_cutoff = timezone.now() - timedelta(days=RECENT_WINDOW_DAYS)
    assigned = Ticket.objects.filter(Agent__isnull=False, Date__gte=recent_cutoff).count()

    context = {
        # Guard against division by zero when no tickets exist yet.
        "closed_ticket_percentage": round(closed / total * 100, 1) if total else 0.0,
        "assigned_ticket_percentage": assigned,
        "closed": closed,
        "open": counts.get("Open", 0),
        "solved": counts.get("Solved", 0),
        "pending": counts.get("Pending", 0),
    }
    return render(request, "home.html", context)


@login_required
def ticket(request):
    """List tickets, scoped to the signed-in role, then searched and filtered.

    Role scoping happens first and the user cannot influence it. Every filter
    below only ever narrows that queryset further, so no combination of query
    parameters can widen what a role is allowed to see.
    """
    if request.user.is_superuser:
        tickets = Ticket.objects.all()
    elif request.user.is_staff:
        tickets = Ticket.objects.filter(Agent=request.user.id)
    else:
        tickets = Ticket.objects.filter(Client=request.user.id)

    search = request.GET.get("q", "").strip()
    if search:
        tickets = tickets.filter(
            Q(Subject__icontains=search)
            | Q(Client__username__icontains=search)
            | Q(Agent__username__icontains=search)
        )

    # Unrecognised values are ignored rather than rejected, so a hand-edited
    # URL degrades to the unfiltered list instead of erroring.
    status = request.GET.get("status", "")
    if status in TicketStatus.values:
        tickets = tickets.filter(Status=status)

    urgent = request.GET.get("urgent", "")
    if urgent in {"yes", "no"}:
        tickets = tickets.filter(Urgent=(urgent == "yes"))

    # One query for the page instead of two per row in the template.
    tickets = tickets.select_related("Client", "Agent")

    # get_page() clamps out-of-range and non-numeric pages instead of raising.
    page = Paginator(tickets, TICKETS_PER_PAGE).get_page(request.GET.get("page"))

    return render(
        request,
        "ticket.html",
        {
            # A Page is iterable, so the existing template loop is unchanged.
            "Tickets": page,
            "page_obj": page,
            "search": search,
            "status": status,
            "urgent": urgent,
            "status_choices": TicketStatus.choices,
            "is_filtered": bool(search or status or urgent),
        },
    )


@login_required
def user(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Only administrators can view the user directory.")

    context = {"Agents": Agent.objects.all(), "Clients": Client.objects.all()}
    return render(request, "user.html", context)


@login_required
def add_ticket(request):
    # Only clients open tickets; agents and admins have no Client record.
    client = Client.objects.filter(pk=request.user.pk).first()
    if client is None:
        raise PermissionDenied("Only clients can open a support ticket.")

    if request.method == "POST":
        form = AddTicketform(request.POST)
        if form.is_valid():
            agent = Agent.objects.filter(Dispo=True).first()
            if agent is None:
                messages.error(
                    request,
                    "No support agent is available right now. Please try again later.",
                )
            else:
                ticket = form.save(commit=False)
                ticket.Client = client
                ticket.Agent = agent
                ticket.Status = "Open"
                ticket.save()
                return redirect("ticket")
    else:
        form = AddTicketform()

    return render(request, "addticket.html", {"form": form})


@login_required
@staff_member_required
def edit_ticket(request, id):
    instance = get_object_or_404(Ticket, pk=id)

    if request.method == "POST":
        form = EditTicketform(request.POST, instance=instance)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.Client = instance.Client
            ticket.Agent = instance.Agent
            ticket.save()
            return redirect("ticket")
    else:
        form = EditTicketform(instance=instance)

    context = {"form": form, "ticket": instance}
    return render(request, "editticket.html", context)


@login_required
@staff_member_required
def delete_ticket(request, id):
    instance = get_object_or_404(Ticket, pk=id)

    instance.delete()
    return redirect("ticket")
