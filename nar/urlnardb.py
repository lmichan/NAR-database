#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import datetime
import numpy as np
import os
import requests
import urllib.request



'''
Este modulo contiene funciones para generar y actualizar archivos csv
con informacion de la pagina https://www.oxfordjournals.org/nar/database/a/
Adicionalmente tambien se incluyen funciones para obtener informacion de
los archivos csv que se generan
'''




####Funciones de ayuda####

def convertir_formato_fecha(date : str):
    month_string = date[3:6]
    if month_string == 'Jan':
        month_number = '01'
    elif month_string == 'Feb':
        month_number = '02'
    elif month_string == 'Mar':
        month_number = '03'
    elif month_string == 'Apr':
        month_number = '04'
    elif month_string == 'May':
        month_number = '05'
    elif month_string == 'Jun':
        month_number = '06'
    elif month_string == 'Jul':
        month_number = '07'
    elif month_string == 'Aug':
        month_number = '08'
    elif month_string == 'Sep':
        month_number = '09'
    elif month_string == 'Oct':
        month_number = '10'
    elif month_string == 'Nov':
        month_number = '11'
    elif month_string == 'Dec':
        month_number = '12'
    return date[-4:] + '-' + month_number + '-' + date[:2]






def obtener_contactos(string : str):
    
    contacts = ''
    i = j = 1
    while i < len(string):
        if string[i-1] == 'f' and string[i] == '=':
            j = i + 2
            while string[j] != '"':
                j += 1
            contacts += ', ' + string[i+2:j] if contacts else string[i+2:j]
            i = j
        i += 1
    contacts = contacts.replace('MAILTO:', '')
    
    if not contacts:
        contacts = string.strip()
    
    return contacts






def sustituir_direcciones_y_correos(string : str):

    s = set()
    for i in range(len(string) - 1):
        if string[i] == '<' and string[i+1] == 'a':
            j = i + 2
            while string[j] != 'a' or string[j+1] != '>':
                j += 1
            s.add(string[i:j+2])
            
    for x in s:
        string = string.replace(x, x[x.find('"')+1:x.rfind('"')])
    string = string.replace('MAILTO:', '')
            
    return string






def sustituir_digitos(string : str):
    
    try:
        s = set()
        for i in range(len(string) - 1):
            if string[i] == '&' and string[i+1] == '#':
                j = i + 2
                while string[j] != ';':
                    j += 1
                s.add(string[i:j+1])
                
        for x in s:
            string = string.replace(x, chr(int(x[2:-1])))
            
    except IndexError:
        pass
        
    return string





def sustituir_caracteres(string : str):    
    return string.replace('<i>', '').replace('</i>', '').replace('<I>', '').replace('</I>', '') \
        .replace('<strong>', '').replace('</strong>', '') \
        .replace('<b>', '').replace('</b>', '').replace('<B>', '').replace('</B>', '') \
        .replace('<sub>2</sub>', '₂').replace('<SUB>2</SUB>', '₂').replace('&amp;', '&') \
        .replace(' </P>', '').replace('</>', '')




def sustituir_superindices(string):
    
    diccionario_superindices = {
    ' ' : '',
    ',' : '‧',
    '+' : '⁺',
    '#' : '',
    '*' : '*',
    '0' : '⁰',
    '1' : '¹',
    '2' : '²',
    '3' : '³',
    '4' : '⁴',
    '5' : '⁵',
    '6' : '⁶',
    '7' : '⁷',
    '8' : '⁸',
    '9' : '⁹',
    '®' : '®',
    '™' : '™',
    'Â' : ''}
    
    i = 0
    s = set()
    while i < len(string)-1:
        if string[i] == '<' and string[i+1].lower() == 's':
            j = i + 5
            while string[j].lower() != 'p' or string[j+1] != '>':
                j += 1
            s.add(string[i:j+2])
            i = j
        i += 1
    
    
    for x in s:
        caracteres = x.replace('<sup>', '').replace('</sup>', '') \
        .replace('<SUP>', '').replace('</SUP>', '').replace('TM', '™')
        superindices = ''
        try:
            for i in range(len(caracteres)):
                superindices += diccionario_superindices[caracteres[i]]
            string = string.replace(x, superindices)
        except KeyError:
            pass

    return string







def sustituir_indicadores_enumeracion(string : str):    
    return string.replace(' <ul style="list-style:circle">', '') \
        .replace(' <ul style="list-style:disc">', '') \
        .replace(' <ul>', '').replace(' </ul> ', '').replace('</ul>', '') \
        .replace('<ol> ', '').replace(' </ol>', '')





def sustituir_saltos_linea(string : str):    
    return string.replace(' <br> ', '\n').replace('<br> ', '\n') \
        .replace(' <br>', '\n').replace('<br>', '\n') \
        .replace(' <br /> ', '\n').replace('<br /> ', '\n') \
        .replace(' <br />', '\n').replace('<br />', '\n') \
        .replace(' <p> ', '\n').replace('<p> ', '\n') \
        .replace(' <p>', '\n').replace('<p>', '\n') \
        .replace('<be />', '\n').replace('</br>', '\n').replace(' <BR', '\n')




def formatear(string : str):
    string = sustituir_direcciones_y_correos(string)
    string = sustituir_digitos(string)
    string = sustituir_caracteres(string)
    string = sustituir_superindices(string)
    string = sustituir_indicadores_enumeracion(string)
    string = sustituir_saltos_linea(string)
    return string


##########################









'''
Escribe un archivo csv con nombre de la forma
NAR Database Summary Paper Alphabetic List aaaa-mm-dd.csv
con la informacion parcial que se encuentra en
https://www.oxfordjournals.org/nar/database/a/
El parametro directory es opcional y es el nombre
del directorio del csv que se genera. En caso de no
proporcionarse el parametro directory el archivo
se genera en el directorio de trabajo actual.
'''
def generar_csv(directory = os.getcwd()):
    
    #Lanzamiento de excepcion si directory no es valida
    if not os.path.isdir(directory):
        raise FileNotFoundError('No such directory path: \'' + directory)
    
    header = ['nombre', 'url nar', 'urls bd en nar y redirigida son distintas', \
               'url bd en nar', 'url bd redirigida', 'codigo status url bd', \
               'ultima modificacion de la pagina de la bd', \
               'categoria 1', 'subcategoria 1', 'categoria 2', 'subcategoria 2', \
               'categoria 3', 'subcategoria 3', 'url doi', 'url redirigida del doi']
    #Creacion de arreglo donde se almacenara la informacion de registros
    rows = np.array([header], dtype=object)
    count = 1
    
    #Lectura de NAR Database Summary Paper Alphabetic List
    protocol_and_host = 'https://www.oxfordjournals.org'
    
    with urllib.request.urlopen(protocol_and_host + '/nar/database/a/', timeout=120) as response1:
        lines = response1.readlines()
       
    #Obtencion de informacion de registros
    for x in lines:
        
        #nombre
        if x.rstrip().endswith(b'</strong>'):
            arr = np.empty(15, dtype='U400')
            arr[0] = formatear(x[x.find(b'>')+1:x.rfind(b'<')].decode('UTF-8').strip())
        
        #url bd en nar
        if x.rstrip().endswith(b'&nbsp; &nbsp; &nbsp;'):
            db_url = x[x.find(b'"')+1:x.rfind(b'"')].decode('UTF-8')
            arr[3] = db_url
        
            if db_url:
                try:
                    with urllib.request.urlopen(db_url, timeout=120) as response3:
                        #url bd redirigida
                        arr[4] = response3.geturl()
                        #urls bd en nar y redirigida son distintas
                        arr[2] = 'True' if db_url != response3.geturl() else 'False'
                        #codigo status url bd
                        arr[5] = response3.getcode()
                        #ultima modificacion de la pagina de la bd
                        last_modified = response3.getheader('Last-Modified')
                        if last_modified != None:
                            arr[6] = convertir_formato_fecha(last_modified[5:16])
                except Exception as e:
                    if '\n' in str(e) and str(e).startswith('HTTP'):
                         arr[5] = str(e)[:str(e).find(':')+2] + str(e)[str(e).rfind('\n')+1:]
                    else:
                        arr[5] = str(e).rstrip()
        
        #url nar
        if x.rstrip().endswith(b'summary </a>'):
            nar_url = protocol_and_host + x[x.find(b'"')+1:x.rfind(b'"')].decode('UTF-8')
            arr[1] = nar_url
            
            with urllib.request.urlopen(nar_url, timeout=120) as response2:
                l = response2.readlines()            
            
            i = 122
            while l[i].strip() != b'<div class="category">':
                i += 1
            
            k = 7
            while l[i].rstrip() != b'<br />':
                #categorias
                if l[i].lstrip().startswith(b'Category: <a href='):
                    if k == 8 or k == 10:
                        k += 1
                    arr[k] = l[i][l[i].find(b'>')+1:l[i].rfind(b'<')].decode('UTF-8')
                    k += 1
                if l[i].lstrip().startswith(b'Subcategory: <a href='):
                    arr[k] = l[i][l[i].find(b'>')+1:l[i].rfind(b'<')].decode('UTF-8')
                    k += 1
                i +=1
            i += 1
            
            while l[i].rstrip() != b'<br />':
                #doi
                if b'doi' in l[i]:
                    doi = l[i][l[i].find(b'"')+1:l[i].rfind(b'"')].decode('UTF-8')
                    arr[13] = doi
                    #url redirigida del doi
                    try:
                        doi_url = requests.get(doi).url
                        if doi_url[doi_url.find(':'):] != doi[doi.find(':'):]:
                            arr[14] = doi_url
                    except Exception as e:
                        arr[14] = str(e)
                i += 1
            
            print(str(count) + ' / 1900 aprox.')
            rows = np.vstack([rows, arr])
            count += 1
    
    #Asignacion de nombre a archivo de salida
    directory += '/NAR Database Summary Paper Alphabetic List ' \
    + datetime.date.today().isoformat() + '.csv'
    
    #Escritura en archivo csv
    with open(directory, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)









'''
Actualiza la informacion de las paginas web de las bases de datos
que se encuentra en un archivo csv con nombre de la forma
NAR Database Summary Paper Alphabetic List aaaa-mm-dd.csv
El parametro path_in es el nombre de la ruta del archivo
cuyo nombre es de la forma
NAR Database Summary Paper Alphabetic List aaaa-mm-dd.csv,
que contiene la informacion a actualizar
El parametro directory es opcional y es el nombre
del directorio del csv que se generara con la informacion actualizada.
En caso de no proporcionarse el parametro directory el archivo
se genera en el directorio de trabajo actual.
'''
def actualizar_csv(path_in : str, directory = os.getcwd()):
    
    #Lanzamiento de excepcion si directory no es valida
    if not os.path.isdir(directory):
        raise FileNotFoundError('No such directory path: \'' + directory)
    
    #Lectura de archivo cuya ruta es path_in en un arreglo
    with open(path_in, newline='') as f:
        rows = np.array(list(csv.reader(f)))
    
    #Actualizacion de informacion de URLs de registros
    for i in range(1, len(rows)):
        
        db_url = rows[i][3]
        if db_url != '':
            try:
                with urllib.request.urlopen(db_url, timeout=120) as response:
                    #url bd redirigida
                    rows[i][4] = response.geturl()
                    #urls bd en nar y redirigida son distintas
                    rows[i][2] = 'True' if db_url != response.geturl() else 'False'
                    #codigo status url bd
                    rows[i][5] = response.getcode()
                    #ultima modificacion de la pagina de la bd
                    last_modified = response.getheader('Last-Modified')
                    if last_modified != None:
                        rows[i][6] = convertir_formato_fecha(last_modified[5:16])
            except Exception as e:
                if '\n' in str(e) and str(e).startswith('HTTP'):
                     rows[i][5] = str(e)[:str(e).find(':')+2] + str(e)[str(e).rfind('\n')+1:]
                else:
                    rows[i][5] = str(e).rstrip()
      
        print(str(i) + '/' + str(len(rows)-1))
        
    #Asignacion de nombre a archivo de salida
    directory += '/NAR Database Summary Paper Alphabetic List ' \
    + datetime.date.today().isoformat() + '.csv'
    
    #Escritura en archivo csv
    with open(directory, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)






'''
Escribe un archivo csv con nombre de la forma
NAR Database Summary Paper Alphabetic List Information aaaa-mm-dd.csv
con la informacion completa que se encuentra en
https://www.oxfordjournals.org/nar/database/a/
El parametro directory es opcional y es el nombre
del directorio del csv que se genera. En caso de no
proporcionarse el parametro directory el archivo
se genera en el directorio de trabajo actual.

Nota: despues de que se obtiene el documento es necesario editar
parte manualmente:
    
Se deben remplazar los simbolos de la izquierda por las secuencias
de caracteres de la derecha que aparecen a continuacion
é &#130
â &#131
ä a&#132
ë e&#137
™ &#153;
¢ &#162
ø &#248
ł &#322

Se debe buscar los registros cuyos id son los numeros que aparecen
a la derecha a continuacion y editar las partes que aparecen en la
izquierda que no se lograron formatear con exito:
'sup>1</sup>', 412
'SUP>3</SUP>', 944
'<sup>1, Bruno W. Sobral<sup>', 1000
'<sup>2</sup></sup>, <sup></sup>3', 1772
'</author>', 316
correo, 600

Se debe identificar los espacios en blanco continuos buscando
tres espacios en blanco seguidos

Se debe reemplazar '<li>' y '</li>'con enumeraciones
'''
def generar_csv_completo(directory = os.getcwd()):
    
    #Lanzamiento de excepcion si directory no es valida
    if not os.path.isdir(directory):
        raise FileNotFoundError('No such directory path: \'' + directory)
        
    header = ['nombre', 'url nar', 'url bd en nar', 'autores', 'instituciones', \
               'contacto', 'descripcion de base de datos', \
               'desarrolladores recientes', 'agradecimientos', 'referencias', \
               'categoria 1', 'subcategoria 1', 'categoria 2', 'subcategoria 2', \
               'categoria 3', 'subcategoria 3', 'url doi']
    #Creacion de arreglo donde se almacenara la informacion de registros
    rows = np.array([header], dtype=object)
    count = 1
    
    #Lectura de NAR Database Summary Paper Alphabetic List
    protocol_and_host = 'https://www.oxfordjournals.org'
    with urllib.request.urlopen(protocol_and_host + '/nar/database/a/', timeout=120) as response1:
        lines = response1.readlines()
    
    #Obtencion de detalle de registros
    for x in lines:
        #nombre
        if x.rstrip().endswith(b'</strong>'):
            arr = np.empty(17, dtype='U11000')
            arr[0] = formatear(x[x.find(b'>')+1:x.rfind(b'<')].decode('UTF-8').strip())
        #url bd en nar
        if x.rstrip().endswith(b'&nbsp; &nbsp; &nbsp;'):
            db_url = x[x.find(b'"')+1:x.rfind(b'"')].decode('UTF-8')
            arr[2] = db_url
        #url nar
        if x.rstrip().endswith(b'summary </a>'):
            nar_url = protocol_and_host + x[x.find(b'"')+1:x.rfind(b'"')].decode('UTF-8')
            arr[1] = nar_url
            
            with urllib.request.urlopen(nar_url, timeout=120) as response2:
                l = response2.readlines()
                        
            i = 122 #123
            
            while not l[i].rstrip().endswith(b'</h3>') and l[i].rstrip() != b'<br />':
                
                #autores 1335
                if l[i].lstrip().startswith(b'<strong>'):
                    arr[3] = formatear(l[i].decode('UTF-8').strip())
                    while not l[i].rstrip().endswith(b'</strong>'):
                        i += 1
                        r = formatear(l[i].decode('UTF-8').strip())
                        arr[3] += ' ' + r if r and arr[3] and not arr[3].endswith('\n') else r
                    arr[3] = arr[3].replace('\n\n', '\n').replace('\r', '').strip()
                #instituciones 72
                elif l[i].strip() == b'<div class="bodytext">' \
                and not l[i+1].lstrip().startswith(b'<strong>') \
                and not l[i+2].lstrip().startswith(b'<span class="subhead">Contact</span>'):
                    i += 1
                    arr[4] = formatear(l[i].decode('UTF-8').strip())
                    while l[i+1].strip() != b'</div>':
                        i += 1
                        r = formatear(l[i].decode('UTF-8').strip())
                        arr[4] += ' ' + r if r and arr[4] and not arr[4].endswith('\n') else r
                    arr[4] = arr[4].replace('\n\n', '\n').replace('\r', '').strip()
                #contacto
                elif l[i].lstrip().startswith(b'<span class="subhead">Contact</span>'):
                    arr[5] = obtener_contactos(l[i].decode('UTF-8'))
                    
                i += 1
            
            while l[i].rstrip() != b'<br />':
                if l[i].rstrip().endswith(b'</h3>'):
                    if l[i].strip() == b'<h3 class="summary">Database Description</h3>':
                        i += 4
                        arr[6] = formatear(l[i].decode('UTF-8').strip())
                        while l[i+1].strip() != b'</div>':
                            i += 1
                            r = formatear(l[i].decode('UTF-8').strip())
                            arr[6] += ' ' + r if r and arr[6] and not arr[6].endswith('\n') else r
                        arr[6] = arr[6].replace('\n\n', '\n').replace('\r', '').strip()
                    elif l[i].strip() == b'<h3 class="summary">Recent Developments</h3>':
                        i += 4
                        arr[7] = formatear(l[i].decode('UTF-8').strip())
                        while l[i+1].strip() != b'</div>':
                            i += 1
                            r = formatear(l[i].decode('UTF-8').strip())
                            arr[7] += ' ' + r if r and arr[7] and not arr[7].endswith('\n') else r
                        arr[7] = arr[7].replace('\n\n', '\n').replace('\r', '').strip()
                    elif l[i].strip() == b'<h3 class="summary">Acknowledgements</h3>':
                        i += 4
                        arr[8] = formatear(l[i].decode('UTF-8').strip())
                        while l[i+1].strip() != b'</div>':
                            i += 1
                            r = formatear(l[i].decode('UTF-8').strip())
                            arr[8] += ' ' + r if r and arr[8] and not arr[8].endswith('\n') else r
                        arr[8] = arr[8].replace('\n\n', '\n').replace('\r', '').strip()
                    elif l[i].strip() == b'<h3 class="summary">References</h3>':
                        i += 4
                        arr[9] = formatear(l[i].decode('UTF-8').strip())
                        while l[i+1].strip() != b'</div>':
                            i += 1
                            r = formatear(l[i].decode('UTF-8').strip())
                            arr[9] += ' ' + r if r and arr[9] and not arr[9].endswith('\n') else r
                        arr[9] = arr[9].replace('\n\n', '\n').replace('\r', '').strip()
                i += 1
                
            i += 1
            
            k = 10
            while l[i].rstrip() != b'<br />':
                #categorias
                if l[i].lstrip().startswith(b'Category: <a href='):
                    if k == 11 or k == 13:
                        k += 1
                    arr[k] = l[i][l[i].find(b'>')+1:l[i].rfind(b'<')].decode('UTF-8')
                    k += 1
                if l[i].lstrip().startswith(b'Subcategory: <a href='):
                    arr[k] = l[i][l[i].find(b'>')+1:l[i].rfind(b'<')].decode('UTF-8')
                    k += 1
                i +=1
                
            i += 1
            
            while l[i].rstrip() != b'<br />':
                #doi
                if b'doi' in l[i]:
                    doi = l[i][l[i].find(b'"')+1:l[i].rfind(b'"')].decode('UTF-8')
                    arr[16] = doi
                i += 1
            
            
            print(str(count) + ' / 1900 aprox.')
            rows = np.vstack([rows, arr])
            count += 1
    
    #Asignacion de nombre a archivo de salida
    directory += '/NAR Database Summary Paper Alphabetic List Information ' \
    + datetime.date.today().isoformat() + '.csv'
    
    #Escritura en archivo csv
    with open(directory, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)







'''
Las funciones que aparecen a continuacion realizan lo que su nombre indica
a partir de un archivo csv cuyo nombre es de la forma
NAR Database Summary Paper Alphabetic List aaaa-mm-dd.csv
y cuya ruta es el argumento path_in
El parametro directory es opcional y es el nombre
del directorio del documento que se generara.
En caso de no proporcionarse el parametro directory el archivo
se genera en el directorio de trabajo actual.
'''

def generar_frecuencias_categoria_subcategoria(path_in : str, directory = os.getcwd()):
    
    #Lectura de archivo csv
    with open(path_in, newline='') as f:
        rows = np.array(list(csv.reader(f)))
    
    d = dict()
    t0 = tuple(['', ''])
    for x in rows[1:]:
        t1 = tuple([x[7], x[8]])
        if t1 != t0:
            d[t1] = d.get(t1, 0) + 1
        t2 = tuple([x[9], x[10]])
        if t2 != t0:
            d[t2] = d.get(t2, 0) + 1
        t3 = tuple([x[11], x[12]])
        if t3 != t0:
            d[t3] = d.get(t3, 0) + 1
    
    l1 = ['categoria', 'subcategoria', 'frecuencia']
    l = [[key[0], key[1], d[key]] for key in d]
    l.sort()

    #Asignacion de nombre a archivo de salida
    directory += '/frecuencias de categorias-subcategorias ' \
    + datetime.date.today().isoformat() + '.csv'
    
    #Escritura en archivo csv
    with open(directory, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(l1)
        writer.writerows(l)






def generar_frecuencias_actualizacion_anio(path_in : str, directory = os.getcwd()):
    
    #Lectura de archivo csv
    with open(path_in, newline='') as f:
        rows = np.array(list(csv.reader(f)))
    
    d = dict()
    for x in rows[:, 6][1:]:
        year = x[:4]
        if year:
            d[year] = d.get(year, 0) + 1
    
    l1 = ['año', 'frecuencia']      
    l = list(d.items())
    l.sort()

    #Asignacion de nombre a archivo de salida
    directory += '/frecuencias de actualizaciones de bases por año ' \
    + datetime.date.today().isoformat() + '.csv'

    #Escritura en archivo csv
    with open(directory, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(l1)
        writer.writerows(l)






def generar_codigos_status_url_bd(path_in : str, directory = os.getcwd()):
    
    #Lectura de archivo cuya ruta es path_in en un arreglo
    with open(path_in, newline='') as f:
        rows = np.array(list(csv.reader(f)))
    
    s = set()
    for x in rows[:, 5][1:]:
        s.add(x + '\n')
    s.discard('\n')
    
    l = list(s)
    l.sort()
    
    
    #Asignacion de nombre a archivo de salida
    directory += '/codigos de status url bd ' \
    + datetime.date.today().isoformat() + '.txt'
    
    #Escritura en archivo csv
    with open(directory, 'w') as f:
        f.writelines(l)






def generar_registros_con_info_repetida(path_in : str, directory = os.getcwd()):

    with open(path_in, newline='') as f:
        rows = np.array(list(csv.reader(f)))
    
    lista_conjuntos = list()
    for i in range(1, len(rows)):
        s = set([ tuple(rows[i]) ])
        for j in range(i+1, len(rows)):
            
            #nombre
            if rows[i][0]:
                if rows[i][0].lower() == rows[j][0].lower():
                    s.add(tuple(rows[j]))
                    
            #url bd en nar
            if rows[i][3]:
                r1, r2 = rows[i][3], rows[j][3]
                if r1.endswith('/'):
                    r1 = r1[:len(r1)-1]   
                if r2.endswith('/'):
                    r2 = r2[:len(r2)-1]
                if r1[r1.find(':')+1:].lower() == r2[r2.find(':')+1:].lower():
                    s.add(tuple(rows[j]))
                    
            #url bd redirigida
            if rows[i][4]:
                r1, r2 = rows[i][4], rows[j][4]
                if r1.endswith('/'):
                    r1 = r1[:len(r1)-1]   
                if r2.endswith('/'):
                    r2 = r2[:len(r2)-1]
                if r1[r1.find(':')+1:].lower() == r2[r2.find(':')+1:].lower():
                    s.add(tuple(rows[j]))
                    
            #url redirigida del doi
            if rows[i][14]:
                if rows[i][14] == rows[j][14]:
                    s.add(tuple(rows[j]))
        
        if len(s) > 1:
            lista_conjuntos.append(s)
    
    indices_excluidos = set()
    for i in range(len(lista_conjuntos)):
        for j in range(i+1, len(lista_conjuntos)):        
            if lista_conjuntos[i] & lista_conjuntos[j]:
                lista_conjuntos[j].update(lista_conjuntos[i])
                indices_excluidos.add(i)
                    
    lista_conjuntos = [list(x) for i, x in enumerate(lista_conjuntos)
                       if i not in indices_excluidos]
    
    for x in lista_conjuntos:
        x.sort()
    lista_conjuntos.sort()
    
    encabezado = ['nombre', 'url nar', 'urls bd en nar y redirigida son distintas', \
           'url bd en nar', 'url bd redirigida', 'codigo status url bd', \
           'ultima modificacion de la pagina de la bd', \
           'categoria 1', 'subcategoria 1', 'categoria 2', 'subcategoria 2', \
           'categoria 3', 'subcategoria 3', 'url doi', 'url redirigida del doi']

    #Asignacion de nombre a archivo de salida
    directory += '/registros en nar con informacion repetida ' \
    + datetime.date.today().isoformat() + '.csv'

    #Escritura en archivo csv
    with open(directory, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(encabezado)
        for grupo in lista_conjuntos:
            for e in grupo:
                writer.writerow(e)
            writer.writerow([])







