from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError

class LibraryLoan(models.Model):
    _name = "library.loan"
    _description = "Library Loan"
    
    book_id = fields.Many2one('library.book', required=True)
    borrower_id = fields.Many2one('res.partner', required=True)
    # scadenza
    due_date = fields.Date(
        string="Due Date",
        default=fields.Date.context_today,
        copy=False,
        required=True
        )
    # prestiti 
    loan_date = fields.Date(
        string="Loan Date",
        default=fields.Date.context_today,
        readonly=True,
        copy=False
    )
    # ritorno
    return_date = fields.Date(
        string="Return Date",
        default=fields.Date.context_today,
        copy=False
    )
    state = fields.Selection(
        selection=[
            ('active','Active'),
            ('overdue', 'Overdue'),
            ('returned', 'Returned'),
        ]
    )
    is_overdue = fields.Boolean(compute="_computed_check_overdue")
    
    @api.depends('due_date', 'state')
    def _computed_check_overdue(self):
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = (record.due_date < today and record.state == 'active')
    
    @api.constrains("book_id")
    def _check_copies_greater_than_zero(self):
        for record in self:
            if record.book_id and record.book_id.available_copies <= 0:
                raise ValidationError(f"This book has no available copies {record.book_id.name},"
                                      "reader can make an reservation.")
            
            
    @api.model_create_multi
    def create(self, vals_list):
        loans = super().create(vals_list)
        for loan in loans:
            if loan.book_id.available_copies <= 0:
                raise ValidationError("This book has no available copies.")
            loan.book_id.available_copies -= 1
            loan.state = 'active'
        return loans
        
    def action_return(self):
        self.ensure_one()
        self.write({
            'return_date': fields.Date.today(),
            'state': 'returned',
        })
        self.book_id.available_copies += 1

        # cerca prima prenotazione in attesa (ordine per data)
        first_reservation = self.env['library.reservation'].search([
            ('book_id', '=', self.book_id.id),
            ('state', '=', 'waiting'),
        ], limit=1, order='reservation_date asc')

        if first_reservation:
            first_reservation.state = 'notified'
            first_reservation._send_notification_email()