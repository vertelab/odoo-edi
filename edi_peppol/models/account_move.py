import logging, traceback, subprocess
from multiprocessing import Process, queues
from odoo import models, api, _, fields

from lxml import etree, objectify
from lxml.etree import Element, SubElement, QName, tostring

_logger = logging.getLogger(__name__)


class Account_Move(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "peppol.toinvoice", "peppol.toorder", "peppol.frominvoice"]
    _description = "Module that facilitates convertion of buissness messages from and to PEPPOL."

    # Button click function comming from Odoo.
    def to_peppol_button(self):
        return self.to_peppol()

    # Button click function comming from Odoo.
    def from_peppol_button(self):
        return self.from_peppol()

    # Converts a account.move to a PEPPOL file.
    # Currently can only handle invoices, but is inteded to handle
    #  all different kinds of messages that PEPPOL can encode.
    def to_peppol(self):
        tree = etree.ElementTree(self.create_invoice())

        tree.write('/usr/share/odoo-edi/edi_peppol/demo/output.xml',
                   xml_declaration=True,
                   encoding='UTF-8',
                   pretty_print=True)

        # TODO: Should be validating here!
        #self.validate('/usr/share/odoo-edi/edi_peppol_base/demo/output.xml')
        #self.validation_thread()

        #self.env['peppol.validate'].validate_peppol('/usr/share/odoo-edi/edi_peppol/demo/output.xml')

    # Converts a account.move from a PEPPOL file.
    # Currently can only handle invoices, but is inteded to handle
    #  all different kinds of messages that PEPPOL can encode.
    def from_peppol(self):
        tree = self.parse_xml('/usr/share/odoo-edi/edi_peppol/demo/output.xml')

        if tree is None:
            return None

        # TODO: Should be validating here!

        temp = self.import_invoice(tree)

        # TODO: Remove this debugg function
        #self.compare_account_moves(115, self.id)

        return temp

    # This is a debugging functions, which is intended to compare
    #  a invoice that is made into a PEPPOL and then back again,
    #  in its before and after states
    def compare_account_moves(self, to_peppol_id, from_peppol_id):
      to_dict = self.extra_account_move_info(to_peppol_id)
      from_dict = self.extra_account_move_info(from_peppol_id)

      for n in to_dict:
        text = f"{n}" + ": " + f"{to_dict[n]}" + " =/= " + f"{from_dict[n]}"
        if to_dict[n] != from_dict[n]:
          _logger.error(text)
        #else:
        #  _logger.warning(text)
      #_logger.warning(to_dict)

    # Helper Function for debugging pruposes
    def extra_account_move_info(self, move_id):
      dict = {}
      move = self.env['account.move'].browse(move_id)
      ingore_list = ['<lamda>', '_ids', '_origin', '_prefetch_ids', 'access_token', 'access_url',
                     'create_date', 'date', 'display_name', 'id', 'ids', 'name', 'write_date',
                     'highest_name', 'show_reset_to_draft', 'state']
      for a in dir(move):
        if not callable(getattr(move,a)):
          if not a.startswith('__'):
            if a not in ingore_list:
              dict.update({a: getattr(move, a)})
      return dict

    # Validates a inputed PEPPOL 'file'
    def validate(self, file):
      p = Process(target=self.validation_thread, args=())
      p.start()
      #p.join()
      _logger.warning("CONTINIUING IN VALIDATE!")

    def validation_thread(self):
      _logger.warning("TRYING TO START SUBPROCESS")
      s = subprocess.check_output(["python3", "/usr/share/odoo-edi/edi_peppol_validate/models/validate_test.py"])
      #s = subprocess.check_output(["echo", "THIS IS A ECHO!"])
      _logger.warning(f"{s=}")
      _logger.warning("FINISHED SUBPROCESS")
      #print("PRINT WORKS")