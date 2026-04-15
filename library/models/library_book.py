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
        compute="_computed_set_state"
    )
    loan_count = fields.Integer()
    
    @api.depends('available_copies')
    def _computed_set_state(self):
        for record in self:
            if record.available_copies > 6:
                record.state = 'available'
            elif record.available_copies > 0:
                record.state = 'partial_available'
            else:
                record.state = 'unavailable'