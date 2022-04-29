import sys, os, logging

from odoo import models, api, _, fields

#from saxonpy import *


_logger = logging.getLogger(__name__)

#_logger.warning("BEFORE saxonpy import")


#sys.path.append("/usr/share")

#sys.path.append("/usr/share/odoo-edi/edi_peppol_validate/models")
#sys.path.append("/usr/share/libsaxon-HEC-11.3/Saxon.C.API/python-saxon")

#sys.path.append("/usr/share")
#sys.path.append("/usr/share/libsaxon-HEC-11.3/Saxon.C.API/python-saxon")
#sys.path.append("/usr/share/odoo-edi/edi_peppol_validate/models")
#sys.path.append("/usr/lib/python38.zip,/usr/lib/python3.8,/usr/lib/python3.8/lib-dynload")
#sys.path.append("/home/bjornhayer/.local/lib/python3.8/site-packages")
#sys.path.append("/usr/local/lib/python3.8/dist-packages")
#sys.path.append("/usr/lib/python3/dist-packages")
#sys.path.append("/usr/share/odoo-edi/edi_peppol_validate/models/python-saxon")

#_logger.warning(os.environ["PYTHONPATH"])
#os.environ["SAXONC_HOME"] = '/usr/share/libsaxon-HEC-11.3'
#os.environ["PYTHONPATH"] = '/usr/share/libsaxon-HEC-11.3/Saxon.C.API/python-saxon'
#_logger.warning("After appends/environ, when sys.path is: " + ','.join(sys.path))
VALIDATE = True
try:
    import saxonpy
    #from saxonpy import *
    #_logger.warning(dir(saxonpy))
    #_logger.warning("saxonpy import statement done")
    #with saxonpy.PySaxonProcessor(license=False) as proc:
    #    _logger.warning(proc.version)
    #_logger.warning(os.listdir('./libsaxon-HEC-11.3/Saxon.C.API/python-saxon'))

    #import importlib.util as ilu
    #folder = './libsaxon-HEC-11.3/Saxon.C.API/python-saxon'
    #file = 'saxonc.pyx'
    #spec = ilu.spec_from_file_location(file, folder)

    #_logger.warning(spec.name)

    #saxonc = ilu.module_from_spec(spec)
    #spec.loader.exec_module(saxonc)

    #from saxonpy import PySaxonProcessor
#    pass
    #from folder1.folder2 import python_saxon as saxonc
    #from . import python_saxon as saxonc 
    #from . import python_saxon
    #_logger.warning(dir(python_saxon))
    #saxonc = python_saxon.saxonc 
    #raise ImportError
except ImportError as e:
    VALIDATE = False    
    _logger.warning(e)
    #_logger.warning("saxonpy import FAILED!")
else:
    #_logger.warning("saxonpy import SUCCEDED!")
    pass

#_logger.warning("AFTER saxonc import")


class PeppolValidate(models.Model):
    _name = "peppol.validate"
    _description = "Module to validate PEPPOL xml files."


    def validate_peppol (self, msg, type=None):
        if type is None:
            type = 'invoice'

        if type == 'invoice':
            self.validate_peppol_invoice(msg)

        return None


    def validate_peppol_invoice (self, msg):
        if not VALIDATE:
            _logger.warning("Validation was not performed as Saxonpy could not be importet. Is Saxopy installed?")
            return False

        #msgName = msg.rsplit('/', 1)[-1].split('.')[0]
        msgName = os.path.basename(msg)

        _logger.warning(f"{msg=}")
        _logger.warning(f"{msgName=}")
        #_logger.warning("Before import PySaxonProcessor")
        
        #_logger.warning("After import PySaxonProcessor")

    #Creation of validation reports
        with saxonpy.PySaxonProcessor(license=False) as proc:
            _logger.warning(proc.version)

            xslt30_processor = proc.new_xslt30_processor()
            #schema_validator = proc.new_schema_validator()

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

    #Checking of validation reports contents

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


    def validate_report_log(self, schema, name):
        validation_successfull = True

        val = self.validate_report(schema)
        if val[0] != '':
            validation_successfull = False
            _logger.warning('\n' + "Validation failed for " + name + ":")
            for n in val:
                _logger.warning(n)

        return validation_successfull


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