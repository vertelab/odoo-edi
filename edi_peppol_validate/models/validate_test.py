from ast import Pass
from lxml import etree
import sys, os, logging, glob

from odoo import models, api, _, fields


_logger = logging.getLogger(__name__)









# TODO: This file is used to manually, with a console command, validate XML PEPPOL files.
# This should be done automaticly. When that is fixed, this file should be removed, untill then,
#  use it with the 'python3 validate_test.py' command,
#  while standing in the edi_peppol_validate/models folder.










#_logger.warning("BEFORE saxonc import, when sys.path is: " + ','.join(sys.path))


#sys.path.append("./python-saxon")
#sys.path.append("/usr/share")
#sys.path.append("/usr/share/libsaxon-HEC-11.3/Saxon.C.API/python-saxon")
#sys.path.append("/usr/share/odoo-edi/edi_peppol_validate/models")
#sys.path.append("/usr/lib/python38.zip,/usr/lib/python3.8,/usr/lib/python3.8/lib-dynload")
#sys.path.append("/home/bjornhayer/.local/lib/python3.8/site-packages")
#sys.path.append("/usr/local/lib/python3.8/dist-packages")
#sys.path.append("/usr/lib/python3/dist-packages")
#_logger.warning(os.environ["PYTHONPATH"])
#os.environ["SAXONC_HOME"] = '/usr/share/libsaxon-HEC-11.3'
#os.environ["PYTHONPATH"] = '/usr/share/libsaxon-HEC-11.3/Saxon.C.API/python-saxon'
#_logger.warning("After appends/environ, when sys.path is: " + ','.join(sys.path))
VALIDATE = True
try:
    #import saxonpy
    from saxonpy import PySaxonProcessor
    _logger.warning("saxonpy import statement done")
    #with PySaxonProcessor(license=False) as proc:
    #    _logger.warning(proc.version)
    #_logger.warning(os.listdir('/usr/share/odoo-edi/edi_peppol_validate/models/python_saxon'))

    #from saxonpy import PySaxonProcessor
    #import saxonpy

    #folder = '/usr/share/odoo-edi/edi_peppol_validate/models/python_saxon/saxonc.pyx'
    #file = 'saxonc'
    #spec = ilu.spec_from_file_location(file, folder)

    #_logger.warning(spec.name)

    #saxonc = ilu.module_from_spec(spec)
    #spec.loader.exec_module(saxonc)
    #import saxonc
except ImportError as e:
    VALIDATE = False
    _logger.warning(e)
    _logger.warning("saxonc import FAILED!")
else:
    _logger.warning("saxonc import SUCCEDED!")


_logger.warning("AFTER saxonc import")



#class PeppolValidate(models.Model):
#    _name = "peppol.validate"


def validate_peppol (msg, type=None):
    if type is None:
        type = 'invoice'

    if type == 'invoice':
        validate_peppol_invoice(msg)

    return None


def validate_peppol_invoice (msg):
    if not VALIDATE:
        _logger.warning("Validation was not performed as saxonpy could not be importet. Is saxonpy installed?")
        return False


    _logger.warning("Inside validate_peppol_invoice")

    #msgName = msg.rsplit('/', 1)[-1].split('.')[0]
    msgName = os.path.basename(msg)

    #_logger.warning("Before import PySaxonProcessor")
    #from saxonpy import PySaxonProcessor
    #_logger.warning("AFter import PySaxonProcessor")

    _logger.warning(f"{msg=}")
    _logger.warning(f"{msgName=}")

    #Checks that the XML is well formed
    try:
        doc = etree.parse(msg)
    except Exception as e:
        _logger.error(e)
        _logger.error("VALIDATION FAILED FOR: " + msg)
        return

#Creation of validation reports
    with PySaxonProcessor(license=False) as proc:
        _logger.warning(proc.version)

        xslt30_processor = proc.new_xslt30_processor()
        #schema_validator = proc.new_schema_validator()

        xslt30_processor.set_cwd(".")

        #out = xslt30_processor.transform_to_string(source_file=msg,
        #                                        stylesheet_file="/usr/share/odoo-edi/edi_peppol_validate/data/stylesheet-ubl.xslt")
        #with open("/usr/share/odoo-edi/edi_peppol_validate/data/temp/report-ubl-" + msgName + ".xml", "w") as f:
        #    f.write(out)


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

    if not validate_report_log("/usr/share/odoo-edi/edi_peppol_validate/data/temp/report-TC434-" + msgName + ".xml", "TC434"):
        validation_successfull = False

    if not validate_report_log("/usr/share/odoo-edi/edi_peppol_validate/data/temp/report-PEPPOL-" + msgName + ".xml", "PEPPOL"):
        validation_successfull = False



    validate_cleanup(True)

    if not validation_successfull:
        _logger.error("VALIDATION FAILED FOR: " + msg)
    else:
        _logger.warning("VALIDATION SUCCESSFUL FOR: " + msg)


    return validation_successfull


def validate_report_log(schema, name):
    validation_successfull = True

    val = validate_report(schema)
    if val[0] != '':
        validation_successfull = False
        _logger.warning('\n' + "Validation failed for " + name + ":")
        for n in val:
            _logger.warning(n)

    return validation_successfull


def validate_cleanup(full=False):
    if full:
        toremove = glob.glob('/usr/share/odoo-edi/edi_peppol_validate/data/temp/*')
        for t in toremove:
            os.remove(t)
        #os.remove("/usr/share/odoo-edi/edi_peppol_validate/data/temp/*")
    else:
        os.remove("/usr/share/odoo-edi/edi_peppol_validate/data/temp/stylesheet-TC434.xslt")
        os.remove("/usr/share/odoo-edi/edi_peppol_validate/data/temp/stylesheet-PEPPOL.xslt")


def validate_report(report):
    with open(report) as f:
        lines = f.readlines()

    xml_string = '<?xml version="1.0" encoding="UTF-8"?>'

    lines[0] = lines[0].replace(xml_string,'')

    return lines


# This points out which file to attempt to validate.
validate_peppol('/usr/share/odoo-edi/edi_peppol/demo/output.xml')