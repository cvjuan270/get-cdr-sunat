# Module Name: my_module.py

import base64
import configparser
import io
import os
import zipfile

from lxml import etree
from requests.exceptions import ConnectionError as ReqConnectionError
from requests.exceptions import HTTPError, InvalidSchema, InvalidURL, ReadTimeout
from zeep import Client, Settings
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken

# Cargar las variables de entorno
config = configparser.ConfigParser()
config.read(".env")


def _unzip_edi_document(z_str):
    buffer = io.BytesIO(z_str)
    zipfile_obj = zipfile.ZipFile(buffer)
    filenames = zipfile_obj.namelist()
    xml_filenames = [x for x in filenames if x.endswith((".xml", ".XML"))]
    filename_to_decode = xml_filenames[0] if xml_filenames else filenames[0]
    content = zipfile_obj.read(filename_to_decode)
    buffer.close()
    return content


def decode_response(soap_response):
    response_tree = etree.fromstring(soap_response)
    if response_tree.find(".//{*}Fault") is not None:
        return {}
    if response_tree.find(".//{*}sendBillResponse") is not None:
        cdr_b64 = response_tree.find(".//{*}applicationResponse").text
        cdr = _unzip_edi_document(base64.b64decode(cdr_b64))
        return {"cdr": cdr}
    if response_tree.find(".//{*}getStatusResponse") is not None:
        code = response_tree.find(".//{*}statusCode").text
        if response_tree.find(".//{*}content") is not None:
            cdr_b64 = response_tree.find(".//{*}content").text
        else:
            cdr = None
        return {"code": code, "cdr": cdr}
    if response_tree.find(".//{*}sendSummaryResponse") is not None:
        ticket = response_tree.find(".//{*}ticket").text
        return {"number": ticket}
    if response_tree.find(".//{*}getStatusCdrResponse") is not None:
        code = response_tree.find(".//{*}statusCode").text
        message = response_tree.find(".//{*}statusMessage").text
        if response_tree.find(".//{*}content") is not None:
            cdr_b64 = response_tree.find(".//{*}content").text
            cdr = _unzip_edi_document(base64.b64decode(cdr_b64))
            return {"code": code, "message": message, "cdr": cdr}
        else:
            return {}
    return {}


def get_sunat_credentials():

    res = {"fault_ns": "soap-env"}
    res.update(
        {
            "wsdl": "https://e-factura.sunat.gob.pe/ol-it-wsconscpegem/billConsultService?wsdl",
            # 'wsdl': _get_sunat_wsdl_test(),
            "token": UsernameToken(
                config["SUNAT"]["RUC"] + config["SUNAT"]["USER"],
                config["SUNAT"]["PASSWORD"],
            ),
        }
    )
    return res


def get_status_cdr_sunat_service(serie, number):
    credentials = get_sunat_credentials()
    transport = Transport(operation_timeout=15, timeout=15)
    try:
        settings = Settings(raw_response=True)
        client = Client(
            wsdl=credentials["wsdl"],
            wsse=credentials["token"],
            transport=transport,
            settings=settings,
        )
        result = client.service.getStatusCdr(
            config["SUNAT"]["RUC"], config["SUNAT"]["DOC_TYPE"], serie, number
        )
        result.raise_for_status()
        print(result.content)

        ## obtener el cdr
        ressult1 = client.service.getStatus(
            config["SUNAT"]["RUC"], config["SUNAT"]["DOC_TYPE"], serie, number
        )
        print(decode_response(ressult1.content))
        ## obtener el cdr fin

    except (ReqConnectionError, HTTPError, InvalidSchema, InvalidURL, ReadTimeout) as e:
        print(e)
        return False
    soap_response = result.content
    soap_response_decoded = decode_response(soap_response) if soap_response else {}
    if soap_response_decoded.get("error"):
        return {
            "error": soap_response_decoded["error"],
            "blocking_level": "error",
            "code": soap_response_decoded.get("code"),
        }

    code = soap_response_decoded.get("code")
    status = "%s|%s" % (code, soap_response_decoded.get("message"))
    cdr = soap_response_decoded.get("cdr")
    ## guardar cdr en archivo
    if cdr:
        ## nombre del archivo con ruc y numero de comprobante
        path = os.path.dirname(os.path.abspath(__file__))
        file_name = (
            "CDR-" + config["SUNAT"]["RUC"] + "-" + serie + "-" + number + ".xml"
        )

        with open(os.path.join(path, file_name), "wb") as f:
            f.write(cdr)
    return {"cdr": cdr, "status": status, "code": code}


def main():
    serie = input("Ingrese serie : ")
    serie = serie.strip()
    lst_nums = input("Ingrese numeros separados por comas [,] : ")
    lst_nums = lst_nums.split(",")
    for num in lst_nums:
        response = get_status_cdr_sunat_service(serie, num)
        if response:
            print(serie + "-" + num, response["code"], response["status"])


if __name__ == "__main__":

    main()
