# Obtener el CDR (Comprobante de Recepción Electrónico) de la SUNAT

## Requisitos
1. python >= 3.10

## Instalación
```
$ git clone https://github.com/cvjuan270/get-cdr-sunat.git

$ cd get-cdr-sunat/

$ python3 -m venv venv

$ source venv/bin/activate

$ pip3 install -r requirements.txt
```

## Configuracion de variables de entorno

1. Crea un archivo .env en la raíz del proyecto.
2. Agrega las siguientes variables de entorno al archivo .env:

```
[SUNAT]
RUC=20000000006
USER=MODDATOS
PASSWORD=moddats
DOC_TYPE=01
```


## Uso
```$ python3 ./main.py```
- Igresar serie a consultar.

```(venv) juand@DESKTOP-7NGM793:~/Descargas/get-cdr-sunat$ python3 ./main.py 
Ingrese serie : FFFI
```
- Ingresar los numeros correlativos a consultar.

```Ingrese numeros separados por comas [,] : 2009,2010```

Respondera con un mensaje en consola y descargara el cdr es el directorio actual
