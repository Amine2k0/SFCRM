"""Tests for the CRM app.

The suite is organised around the risk in the application rather than around
its files. Permission boundaries come first: the views scope every queryset by
role, and a mistake there leaks one customer's support history to another.
"""

from datetime import timedelta

from django.test import Client as HttpClient
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Agent, Client, Ticket


def make_client(username, password="clientpass123"):
    """Create a Client. Client has no save() override, so hash explicitly."""
    user = Client(username=username, age=30, adress="Somewhere")
    user.set_password(password)
    user.save()
    return user


def make_agent(username, password="agentpass123", available=True):
    """Create an Agent.

    Agent.save() calls set_password() on first save, so the raw password is
    assigned to .password and hashed by the model rather than here.
    """
    user = Agent(username=username, is_staff=True, Dispo=available, age=30, adress="HQ")
    user.password = password
    user.save()
    return user


def make_admin(username="admin", password="adminpass123"):
    return Client.objects.create_superuser(
        username=username, password=password, age=0, adress=""
    )


def sign_in(username, password):
    """Return a test client already logged in as the given user."""
    http = HttpClient()
    assert http.login(username=username, password=password), f"login failed for {username}"
    return http


class AuthenticationTests(TestCase):
    def test_register_creates_a_client_and_logs_them_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newcustomer",
                "age": 41,
                "adress": "12 Rue de la Paix",
                "password1": "a-strong-passphrase-42",
                "password2": "a-strong-passphrase-42",
            },
        )
        self.assertRedirects(response, reverse("ticket"))
        self.assertTrue(Client.objects.filter(username="newcustomer").exists())
        # Registration should authenticate, not just create the row.
        created = Client.objects.get(username="newcustomer")
        self.assertEqual(int(self.client.session["_auth_user_id"]), created.pk)

    def test_register_rejects_mismatched_passwords(self):
        self.client.post(
            reverse("register"),
            {
                "username": "sloppy",
                "age": 20,
                "adress": "x",
                "password1": "a-strong-passphrase-42",
                "password2": "a-different-passphrase-43",
            },
        )
        self.assertFalse(Client.objects.filter(username="sloppy").exists())

    def test_login_with_valid_credentials_redirects_to_tickets(self):
        make_client("alice")
        response = self.client.post(
            reverse("login"), {"username": "alice", "password": "clientpass123"}
        )
        self.assertRedirects(response, reverse("ticket"))

    def test_login_with_bad_password_shows_an_error_and_does_not_authenticate(self):
        make_client("alice")
        response = self.client.post(
            reverse("login"), {"username": "alice", "password": "wrong-password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid Login")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_superuser_login_lands_on_the_dashboard(self):
        make_admin()
        response = self.client.post(
            reverse("login"), {"username": "admin", "password": "adminpass123"}
        )
        self.assertRedirects(response, reverse("home"))

    def test_logout_clears_the_session(self):
        make_client("alice")
        http = sign_in("alice", "clientpass123")
        http.get(reverse("logout"))
        self.assertNotIn("_auth_user_id", http.session)

    def test_anonymous_users_are_redirected_to_login(self):
        for route in ["home", "ticket", "user", "addticket"]:
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertRedirects(
                    response, f"{reverse('login')}?next={reverse(route)}"
                )


class PermissionBoundaryTests(TestCase):
    """The views must refuse, not merely hide, what a role may not see."""

    @classmethod
    def setUpTestData(cls):
        cls.customer = make_client("alice")
        cls.agent = make_agent("agent1")
        cls.admin = make_admin()

    def test_client_cannot_reach_the_dashboard(self):
        http = sign_in("alice", "clientpass123")
        self.assertEqual(http.get(reverse("home")).status_code, 403)

    def test_client_cannot_reach_the_user_directory(self):
        http = sign_in("alice", "clientpass123")
        self.assertEqual(http.get(reverse("user")).status_code, 403)

    def test_agent_cannot_reach_the_dashboard(self):
        http = sign_in("agent1", "agentpass123")
        self.assertEqual(http.get(reverse("home")).status_code, 403)

    def test_agent_cannot_open_a_ticket(self):
        """Agents have no Client record; the view must refuse rather than 500."""
        http = sign_in("agent1", "agentpass123")
        self.assertEqual(http.get(reverse("addticket")).status_code, 403)

    def test_client_cannot_edit_a_ticket(self):
        ticket = Ticket.objects.create(
            Subject="Broken printer", Status="Open", Client=self.customer, Agent=self.agent
        )
        http = sign_in("alice", "clientpass123")
        response = http.get(reverse("editticket", args=[ticket.id]))
        # staff_member_required bounces non-staff to the admin login.
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.get(pk=ticket.id).Status, "Open")

    def test_client_cannot_delete_a_ticket(self):
        ticket = Ticket.objects.create(
            Subject="Broken printer", Status="Open", Client=self.customer, Agent=self.agent
        )
        http = sign_in("alice", "clientpass123")
        http.get(reverse("deleteticket", args=[ticket.id]))
        self.assertTrue(Ticket.objects.filter(pk=ticket.id).exists())

    def test_admin_reaches_every_admin_page(self):
        http = sign_in("admin", "adminpass123")
        for route in ["home", "user", "ticket"]:
            with self.subTest(route=route):
                self.assertEqual(http.get(reverse(route)).status_code, 200)


class TicketVisibilityTests(TestCase):
    """The queryset scoping in ticket() is the app's data-isolation boundary."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = make_client("alice")
        cls.bob = make_client("bob")
        cls.agent_one = make_agent("agent1")
        cls.agent_two = make_agent("agent2")
        cls.admin = make_admin()

        cls.alice_ticket = Ticket.objects.create(
            Subject="Alice cannot print", Status="Open",
            Client=cls.alice, Agent=cls.agent_one,
        )
        cls.bob_ticket = Ticket.objects.create(
            Subject="Bob cannot log in", Status="Open",
            Client=cls.bob, Agent=cls.agent_two,
        )

    def test_a_client_sees_only_their_own_tickets(self):
        http = sign_in("alice", "clientpass123")
        tickets = http.get(reverse("ticket")).context["Tickets"]
        self.assertQuerySetEqual(tickets, [self.alice_ticket])

    def test_a_client_cannot_see_another_clients_ticket_subject(self):
        http = sign_in("alice", "clientpass123")
        response = http.get(reverse("ticket"))
        self.assertContains(response, "Alice cannot print")
        self.assertNotContains(response, "Bob cannot log in")

    def test_an_agent_sees_only_tickets_assigned_to_them(self):
        http = sign_in("agent1", "agentpass123")
        tickets = http.get(reverse("ticket")).context["Tickets"]
        self.assertQuerySetEqual(tickets, [self.alice_ticket])

    def test_an_admin_sees_every_ticket(self):
        http = sign_in("admin", "adminpass123")
        tickets = http.get(reverse("ticket")).context["Tickets"]
        self.assertCountEqual(tickets, [self.alice_ticket, self.bob_ticket])


class TicketLifecycleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = make_client("alice")
        cls.agent = make_agent("agent1")

    def test_client_opens_a_ticket_and_it_is_assigned_and_opened(self):
        http = sign_in("alice", "clientpass123")
        response = http.post(reverse("addticket"), {"Subject": "Screen flickers"})
        self.assertRedirects(response, reverse("ticket"))

        ticket = Ticket.objects.get(Subject="Screen flickers")
        self.assertEqual(ticket.Client, self.customer)
        self.assertEqual(ticket.Agent, self.agent)
        self.assertEqual(ticket.Status, "Open")

    def test_opening_a_ticket_with_no_available_agent_is_reported_not_crashed(self):
        """Previously indexed the empty agent queryset with [0] and raised IndexError."""
        Agent.objects.update(Dispo=False)
        http = sign_in("alice", "clientpass123")
        response = http.post(reverse("addticket"), {"Subject": "Screen flickers"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.count(), 0)
        self.assertContains(response, "No support agent is available")

    def test_agent_updates_a_ticket_status(self):
        ticket = Ticket.objects.create(
            Subject="Screen flickers", Status="Open",
            Client=self.customer, Agent=self.agent,
        )
        http = sign_in("agent1", "agentpass123")
        response = http.post(
            reverse("editticket", args=[ticket.id]),
            {"Subject": ticket.Subject, "Status": "Closed"},
        )
        self.assertRedirects(response, reverse("ticket"))
        self.assertEqual(Ticket.objects.get(pk=ticket.id).Status, "Closed")

    def test_editing_preserves_the_original_client_and_agent(self):
        ticket = Ticket.objects.create(
            Subject="Screen flickers", Status="Open",
            Client=self.customer, Agent=self.agent,
        )
        http = sign_in("agent1", "agentpass123")
        http.post(
            reverse("editticket", args=[ticket.id]),
            {"Subject": "Screen flickers badly", "Status": "Pending"},
        )
        updated = Ticket.objects.get(pk=ticket.id)
        self.assertEqual(updated.Client, self.customer)
        self.assertEqual(updated.Agent, self.agent)

    def test_agent_deletes_a_ticket(self):
        ticket = Ticket.objects.create(
            Subject="Screen flickers", Status="Open",
            Client=self.customer, Agent=self.agent,
        )
        http = sign_in("agent1", "agentpass123")
        self.assertRedirects(
            http.get(reverse("deleteticket", args=[ticket.id])), reverse("ticket")
        )
        self.assertFalse(Ticket.objects.filter(pk=ticket.id).exists())

    def test_editing_a_missing_ticket_is_a_404(self):
        http = sign_in("agent1", "agentpass123")
        self.assertEqual(http.get(reverse("editticket", args=[9999])).status_code, 404)


class DashboardMetricsTests(TestCase):
    """The dashboard previously used raw SQL that broke on an empty table."""

    @classmethod
    def setUpTestData(cls):
        cls.customer = make_client("alice")
        cls.agent = make_agent("agent1")
        make_admin()

    def dashboard(self):
        return sign_in("admin", "adminpass123").get(reverse("home"))

    def open_tickets(self, **counts):
        for status, how_many in counts.items():
            for index in range(how_many):
                Ticket.objects.create(
                    Subject=f"{status} {index}", Status=status.capitalize(),
                    Client=self.customer, Agent=self.agent,
                )

    def test_empty_database_does_not_divide_by_zero(self):
        response = self.dashboard()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["closed_ticket_percentage"], 0.0)

    def test_status_counts_are_reported_per_status(self):
        self.open_tickets(open=3, pending=2, solved=1, closed=4)
        context = self.dashboard().context
        self.assertEqual(context["open"], 3)
        self.assertEqual(context["pending"], 2)
        self.assertEqual(context["solved"], 1)
        self.assertEqual(context["closed"], 4)

    def test_closed_percentage_is_the_share_of_all_tickets(self):
        self.open_tickets(open=1, closed=1)
        self.assertEqual(self.dashboard().context["closed_ticket_percentage"], 50.0)

        Ticket.objects.update(Status="Closed")
        self.assertEqual(self.dashboard().context["closed_ticket_percentage"], 100.0)

    def test_assigned_count_covers_a_rolling_window_not_a_fixed_date(self):
        """The raw SQL hardcoded '2024-5-8', which silently ages out."""
        self.open_tickets(open=2)
        self.assertEqual(self.dashboard().context["assigned_ticket_percentage"], 2)

        # Age one ticket past the window. Date is auto_now_add, so update() is
        # the only way to move it.
        stale = Ticket.objects.first()
        Ticket.objects.filter(pk=stale.pk).update(
            Date=timezone.now() - timedelta(days=90)
        )
        self.assertEqual(self.dashboard().context["assigned_ticket_percentage"], 1)


class ModelTests(TestCase):
    def test_agent_password_is_hashed_on_creation(self):
        agent = make_agent("agent1", password="agentpass123")
        self.assertNotEqual(agent.password, "agentpass123")
        self.assertTrue(agent.check_password("agentpass123"))

    def test_agents_default_to_available(self):
        self.assertTrue(Agent(username="x").Dispo)

    def test_ticket_records_its_creation_time(self):
        ticket = Ticket.objects.create(
            Subject="x", Status="Open",
            Client=make_client("alice"), Agent=make_agent("agent1"),
        )
        self.assertIsNotNone(ticket.Date)
