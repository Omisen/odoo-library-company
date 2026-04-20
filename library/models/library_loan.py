from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LibraryLoan(models.Model):
    _name = "library.loan"
    _description = "Library Loan"
    _order = "loan_date desc, id desc"

    book_id = fields.Many2one(
        "library.book",
        required=True,
        domain=[("available_copies", ">", 0)],
    )
    borrower_id = fields.Many2one("res.partner", required=True)
    due_date = fields.Date(
        string="Due Date",
        default=fields.Date.context_today,
        copy=False,
        required=True,
    )
    loan_date = fields.Date(
        string="Loan Date",
        default=fields.Date.context_today,
        readonly=True,
        copy=False,
    )
    return_date = fields.Date(
        string="Return Date",
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ("active", "Active"),
            ("overdue", "Overdue"),
            ("returned", "Returned"),
        ],
        default="active",
        required=True,
        copy=False,
    )
    is_overdue = fields.Boolean(compute="_compute_is_overdue")

    @api.depends("due_date", "state")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = bool(
                record.due_date and record.state != "returned" and record.due_date < today
            )

    @api.constrains("due_date", "loan_date")
    def _check_dates(self):
        for record in self:
            if record.due_date and record.loan_date and record.due_date < record.loan_date:
                raise ValidationError(_("The due date cannot be earlier than the loan date."))

    def _sync_overdue_state(self):
        today = fields.Date.context_today(self)
        for record in self.filtered(lambda loan: loan.state != "returned"):
            record.state = "overdue" if record.due_date and record.due_date < today else "active"

    @api.model_create_multi
    def create(self, vals_list):
        today = fields.Date.context_today(self)
        for vals in vals_list:
            book = self.env["library.book"].browse(vals.get("book_id"))
            if not book.exists():
                raise ValidationError(_("Please select a valid book."))
            if book.available_copies <= 0:
                raise ValidationError(_("This book has no available copies. Create a reservation instead."))

            loan_date = fields.Date.to_date(vals.get("loan_date")) or today
            due_date = fields.Date.to_date(vals.get("due_date")) or loan_date
            if due_date < loan_date:
                raise ValidationError(_("The due date cannot be earlier than the loan date."))

            vals.setdefault("loan_date", today)
            vals.setdefault("state", "active")

        loans = super().create(vals_list)
        for loan in loans:
            loan.book_id.available_copies -= 1
        loans._sync_overdue_state()
        return loans

    def write(self, vals):
        if "book_id" in vals or "borrower_id" in vals:
            for loan in self.filtered(lambda l: l.state != "returned"):
                raise UserError(_("To change the book or borrower, create a new loan instead."))

        result = super().write(vals)
        if "due_date" in vals or "state" in vals:
            self._sync_overdue_state()
        return result

    def unlink(self):
        for loan in self:
            if loan.state != "returned" and loan.book_id:
                loan.book_id.available_copies += 1
        return super().unlink()

    def action_return(self):
        self.ensure_one()
        if self.state == "returned":
            raise UserError(_("This loan has already been returned."))

        self.write({
            "return_date": fields.Date.context_today(self),
            "state": "returned",
        })
        self.book_id.available_copies += 1

        reservation_model = self.env["library.reservation"]
        notify_next = getattr(reservation_model, "_notify_next_reservation", None)
        if callable(notify_next):
            notify_next(self.book_id)
        return True