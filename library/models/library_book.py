from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LibraryBook(models.Model):
    _name = "library.book"
    _description = "Library Book"
    _order = "name"

    name = fields.Char(required=True)
    authors_ids = fields.Many2many("res.partner", string="Authors")
    category_id = fields.Many2one("library.category", string="Category")
    isbn = fields.Char(string="ISBN")
    available_copies = fields.Integer(default=1)
    state = fields.Selection(
        selection=[
            ("available", "Available"),
            ("partial_available", "Partial Available"),
            ("unavailable", "Unavailable"),
        ],
        compute="_compute_state",
        store=True,
        default="unavailable",
    )
    loan_ids = fields.One2many("library.loan", "book_id", string="Loans")
    reservation_ids = fields.One2many("library.reservation", "book_id", string="Reservations")
    loan_count = fields.Integer(string="Loans Count", compute="_compute_loan_count")
    reservation_count = fields.Integer(string="Reservation Count", compute="_compute_reservation_count")

    @api.constrains("available_copies")
    def _check_available_copies(self):
        for record in self:
            if record.available_copies < 0:
                raise ValidationError(_("Available copies cannot be negative."))

    @api.depends("available_copies")
    def _compute_state(self):
        for record in self:
            if record.available_copies <= 0:
                record.state = "unavailable"
            elif record.available_copies == 1:
                record.state = "partial_available"
            else:
                record.state = "available"

    @api.depends("loan_ids")
    def _compute_loan_count(self):
        for record in self:
            record.loan_count = len(record.loan_ids)

    @api.depends("reservation_ids.state")
    def _compute_reservation_count(self):
        for record in self:
            record.reservation_count = len(
                record.reservation_ids.filtered(lambda r: r.state in ("waiting", "notified"))
            )

    def _open_related_records(self, action_xmlid, res_model, action_name):
        self.ensure_one()
        action = self.env.ref(action_xmlid, raise_if_not_found=False)
        if action:
            action_vals = action.sudo().read()[0]
        else:
            action_vals = {
                "type": "ir.actions.act_window",
                "name": action_name,
                "res_model": res_model,
                "view_mode": "list,form",
            }
        action_vals["domain"] = [("book_id", "=", self.id)]
        action_vals["context"] = dict(self.env.context, default_book_id=self.id)
        return action_vals

    def action_view_loans(self):
        return self._open_related_records(
            "library.view_library_loan_action",
            "library.loan",
            _("Loans"),
        )

    def action_view_reservation(self):
        return self.action_view_reservations()

    def action_view_reservations(self):
        return self._open_related_records(
            "library.view_library_reservetion_action",
            "library.reservation",
            _("Reservations"),
        )
