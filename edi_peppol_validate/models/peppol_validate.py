from ast import Pass

import sys, os, logging

from odoo import models, api, _, fields

_logger = logging.getLogger(__name__)

try:
    import saxonpy
except ImportError as e:
    VALIDATE = False
    _logger.error(e)
else:
    VALIDATE = True



class PeppolValidate(models.Model):
    _name = "peppol.validate"
    _description = "Module to validate PEPPOL xml files."

    # Debug function to help ddebug the validate
    def validate_debug(self):
        _logger.warning(f"{os.getenv('SAXONC_HOME')=}")
        import cython
        from saxonpy import PySaxonProcessor
        _logger.warning("Trying to start PySaxonProcessor.")
        _logger.warning(f"{os.getenv('SAXONC_HOME')=}")
        try:
            _logger.warning("Inside Try")
            proc = PySaxonProcessor(license=False)
            _logger.warning(proc.version)
        except Exception as e:
            _logger.error(e)
        finally:
            _logger.warning("Done with try.")
        return None


    # TODO: Should be updated to work with more types then invoices.
    def validate_peppol (self, msg, type=None):
        #self.validate_debug()
        #return None

        if type is None:
            type = 'invoice'

        if type == 'invoice':
            self.validate_peppol_invoice(msg)

        return None


    # Validates a peppol file given as a file location in 'msg'.
    # TODO: Change this to work off a memmory object, rather then a external file.
    def validate_peppol_invoice (self, msg):
        if not VALIDATE:
            _logger.warning('Validation was not performed as Saxonpy could not be imported. ' +
                            'Is Saxopy installed?')
            return False

        msgName = os.path.basename(msg)

        _logger.warning(f"{msg=}")
        _logger.warning(f"{msgName=}")

        # Creation of validation reports
        # TODO: This part crashen, when run within Odoo. Get it working.
        # TODO: New files are created for the validation. Do this entierly withing memmory instead?
        with saxonpy.PySaxonProcessor(license=False) as proc:
            _logger.warning(proc.version)

            xslt30_processor = proc.new_xslt30_processor()

            xslt30_processor.set_cwd(".")

            out = xslt30_processor.transform_to_string(source_file=msg,
                                                    stylesheet_file="/usr/share/odoo-edi/edi_peppol_validate/data/stylesheet-ubl.xslt")
            with open("/usr/share/odoo-edi/edi_peppol_validate/data/temp/report-ubl-" + msgName + ".xml", "w") as f:
                f.write(out)


            out = xslt30_processor.transform_to_string(source_file="/usr/share/odoo-edi/edi_peppol_validate/data/CEN-EN16931-UBL.sch",
                                                    stylesheet_file="/usr/share/odoo-edi/edi_peppol_validate/data/iso_schematron_skeleton_for_saxon.xsl")
            with open("/usr/share/odoo-edi/edi_peppol_validate/data/temp/stylesheet-TC434.xslt", "w") as f:
                f.write(out)

            xslt30_processor.transform_to_file(source_file=msg,
                                            stylesheet_file="/usr/share/odoo-edi/edi_peppol_validate/data/temp/stylesheet-TC434.xslt",
                                            output_file="/usr/share/odoo-edi/edi_peppol_validate/data/temp/report-TC434-" + msgName + ".xml")


            out = xslt30_processor.transform_to_string(source_file="/usr/share/odoo-edi/edi_peppol_validate/data/PEPPOL-EN16931-UBL.sch",
                                                    stylesheet_file="/usr/share/odoo-edi/edi_peppol_validate/data/iso_schematron_skeleton_for_saxon.xsl")
            with open("/usr/share/odoo-edi/edi_peppol_validate/data/temp/stylesheet-PEPPOL.xslt", "w") as f:
                f.write(out)

            xslt30_processor.transform_to_file(source_file=msg,
                                            stylesheet_file="/usr/share/odoo-edi/edi_peppol_validate/data/temp/stylesheet-PEPPOL.xslt",
                                            output_file="/usr/share/odoo-edi/edi_peppol_validate/data/temp/report-PEPPOL-" + msgName + ".xml")

    # Checking of validation reports contents
        validation_successfull = True

        if not self.validate_report_log("/usr/share/odoo-edi/edi_peppol_validate/data/temp/report-TC434-" + msgName + ".xml", "TC434"):
            validation_successfull = False

        if not self.validate_report_log("/usr/share/odoo-edi/edi_peppol_validate/data/temp/report-PEPPOL-" + msgName + ".xml", "PEPPOL"):
            validation_successfull = False

        self.validate_cleanup()

        if not validation_successfull:
            _logger.warning("VALIDATION FAILED FOR: " + msg)
        else:
            _logger.warning("VALIDATION SUCCESSFUL FOR: " + msg)

        return validation_successfull


    # Help functions
    def validate_report_log(self, schema, name):
        validation_successfull = True

        val = self.validate_report(schema)
        if val[0] != '':
            validation_successfull = False
            _logger.warning('\n' + "Validation failed for " + name + ":")
            for n in val:
                _logger.warning(n)

        return validation_successfull


    # TODO: If the above functions are changed to keep the rapport within 'memmory' and
    #  dosen't change the files, then this function must be changed as well.
    def validate_cleanup(self, full=False):
        if full:
            os.remove("/usr/share/odoo-edi/edi_peppol_validate/data/temp/*")
        else:
            os.remove("/usr/share/odoo-edi/edi_peppol_validate/data/temp/stylesheet-TC434.xslt")
            os.remove("/usr/share/odoo-edi/edi_peppol_validate/data/temp/stylesheet-PEPPOL.xslt")


    def validate_report(self, report):
        with open(report) as f:
            lines = f.readlines()

        xml_string = '<?xml version="1.0" encoding="UTF-8"?>'

        lines[0] = lines[0].replace(xml_string,'')

        return lines