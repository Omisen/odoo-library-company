from odoo import fields, models, api


class LibraryBook(models.Model):
    _name = "library.book"
    _description = "Library Book"

    name = fields.Char(required=True)
    authors_ids = fields.Many2many("res.partner")
    category_id = fields.Many2one("library.category")
    isbn = fields.Char()
    available_copies = fields.Integer(default=1)
    state = fields.Selection(
        selection=[
            ("available", "Available"),
            ("partial_available", "Partial Available"),
            ("unavailable", "Unavailable"),
        ],
        compute="_computed_set_state",
        store=True,
        default="unavailable"
    )
    loan_ids = fields.One2many("library.loan", "book_id", string="Loans")
    loan_count = fields.Integer(string="Loans Count", compute="_compute_loan_count")

    @api.depends("available_copies")
    def _computed_set_state(self):
        for record in self:
            if record.available_copies >= 6:
                record.state = "available"
            elif record.available_copies > 0:
                record.state = "partial_available"
            else:
                record.state = "unavailable"

    @api.depends("loan_ids")
    def _compute_loan_count(self):
        for record in self:
            record.loan_count = len(record.loan_ids)

    # quando su click odoo apre tutti i prestiti di libro e funzione prende solo un libro, cerca azione dei prestiti e
    # poi mette filtro sul libro giusto
    # e apre schermata con solo quei prestiti
    def action_view_loans(self):
        self.ensure_one()
        action = self.env.ref("library.view_library_loan_action").read()[0]
        action["domain"] = [("book_id", "=", self.id)]
        action["context"] = dict(self.env.context, default_book_id=self.id)
        return action
    