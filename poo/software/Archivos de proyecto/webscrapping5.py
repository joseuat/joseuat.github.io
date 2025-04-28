from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import spacy
import mysql.connector
from collections import OrderedDict #Modulo eliminar duplicados de una lista y mantener su orden
import time

#Datos necesarios para hacer la conexion con la base de datos
db=mysql.connector.connect(host='localhost',
                           user='root',
                           passwd='2Rodri10',
                           auth_plugin='mysql_native_password',
                           database='pruebaconferencias3')

#Importamos spacy y cargamos la version en español
nlp=spacy.load('es_core_news_lg')

#Modulo busqueda de elementos
def busqueda():
    #Encontrar titulo
    titulo=soup.find('h1', class_='entry-title').text

    #Categoria
    categoria='Otro'
    if "matutina" in titulo:
        categoria='Mañanera'
    elif 'Asamblea' in titulo:
        categoria = 'Asamblea'
    elif 'Reunión' in titulo:
        categoria = 'Reunion'
    elif 'Aniversario' in titulo:
        categoria = 'Aniversario'
    elif 'Discurso' in titulo:
        categoria = 'Discurso'
    elif 'Recepción' in titulo:
        categoria = 'Recepcion'
    elif 'Inauguración' in titulo:
        categoria = 'Inauguracion'
    elif 'Dialogo' in titulo:
        categoria = 'Dialogo'
    elif 'Día' in titulo:
        categoria = 'Conmemoracion'
    else:
        categoria='Otro'

    #Fecha
    fecha=soup.find('span', class_='entry-date').text
    #Tratamiento de la fecha para concordar con el formato en la base de datos
    fecha1=fecha.replace(',','')
    fecha2=fecha1.split(' ')
    if fecha2[0]=='enero':
        fecha2[0] = '1'
    elif fecha2[0] == 'febrero':
        fecha2[0]='2'
    elif fecha2[0] == 'marzo':
        fecha2[0] = '3'
    elif fecha2[0] == 'abril':
        fecha2[0]='4'
    elif fecha2[0] == 'mayo':
        fecha2[0]='5'
    elif fecha2[0] == 'junio':
        fecha2[0]='6'
    elif fecha2[0] == 'julio':
        fecha2[0]='7'
    elif fecha2[0] == 'agosto':
        fecha2[0]='8'
    elif fecha2[0] == 'septiembre':
        fecha2[0]='9'
    elif fecha2[0] == 'octubre':
        fecha2[0]='10'
    elif fecha2[0] == 'noviembre':
        fecha2[0]='11'
    elif fecha2[0] == 'diciembre':
        fecha2[0]='12'
    fecha3=fecha2[2]+'-'+fecha2[0]+'-'+fecha2[1]

    #Subtitulo
    sub_crudo=soup.find('p', class_='has-text-align-right has-small-font-size')
    sub=''
    if sub_crudo is not None:
        try:
            sub=sub_crudo.em.text
        except:
            sub=sub_crudo.text
    elif sub_crudo is None:
        sub_crudo = soup.find('p', class_='has-text-align-right')
        if sub_crudo is not None:
            try:
                sub = sub_crudo.em.text
            except:
                sub = sub_crudo.text
    else:
        sub=''

    #Separacion de subtitulo en año y texto
    if sub != '':
        if ':' in sub:
            sub=sub.split(':')
        elif ',' in sub:
            sub = sub.split(',')
        else:
            sub = [0000, '']
    else:
        sub=[0000,'']

    #Etiquetas
    tags=soup.find('div', class_='entry-tags tw-meta')
    #Vacias las etiquetas en una lista
    lista_etiquetas=[]#Contiene todas las etiquetas encontradas
    if tags is not None:
        for tag in tags:
            lista_etiquetas.append(tag.text)

    #Texto para procesamiento
    texto=soup.find('div',class_='entry-content')
    #Esta funcion recupera el contenido de la etiqueta div la cual contiene el texto de la nota

    #Participantes
    #Primero se buscara a todos los textos resaltados en negritas
    #Palabras que estan en <p>STRONG, (negritas)
    negritas=texto.find_all('strong')
    '''negritas contiene todos las palabras resaltadas en negritas, solo son AMLO, locutor y pregunta'''

    #En la siguiente lista se guardaran los nombres de los entrevistadores
    entrevistadores=[]

    #En la siguiente lista se guardaran los participantes de la conferencia por parte del gobierno
    #Se comparara los textos en negritas encontrados contra la lista posibles_pant para remover textos no validos
    participant=[]
    posibles_pant=['PRESIDENTE ANDRÉS MANUEL LÓPEZ OBRADOR:','(INICIA VIDEO)','VOZ DE HOMBRE:','VOZ','HOMBRE:',
                   ' HOMBRE:','INTERVENCIÓN ', 'VOZ HOMBRE:','INTERLOCUTORA:','INTERLOCUTOR:','(FINALIZA VIDEO)',
                   ':','INTERVENCIÓN','VOZ ','+++++','INTERVENCIÓN','VOCES A CORO','PREGUNTA','MUJER', 'VOZ MUJER',
                   'VOZ DE MUJER','PRESIDENTE ANDRÉS MANUEL LÓPEZ OBRADOR','Autoridades civiles','Mexicanas',
                   'Mexicanos','mexicanas','mexicanos','Amigas','Amigos','amigas','amigos','militares','-']
    #Esta lista contiene todos los medios que asistieron a la mañanera
    medios=[]
    auxiliar=[]

    #Buscar texto despues de cada palabra PREGUNTA en negritas
    for negro in negritas:
        #El texto en negritas PREGUNTA, indica el inicio de una participacion, generalmente se presentan despues de saludar.
        if negro.text == 'PREGUNTA:':
            #en la variable temporal se guarda el resultado de find_next, que busca el siguiente elemento despues de un texto
            #PREGUNTA en negritas
            #posteriormente se indica que se quiere solo el texto del elemento, este elemento se divide por ','
            temporal=negro.find_next().text.split(',')
            #El primer elemento de la lista resultante generalmente contiene el nombre del entrevistador, se guarda el elemento
            #0 de la lista
            entrevistadores.append(temporal[0])

            #Para obtener los medios a los que pertenece cada reportero primero se necesita acceder al elemento siguiente
            #que donde se encuentra el texto PREGUNTA, se guarda en etiqueta_p
            etiqueta_p=negro.find_next()
            #Ahora los nombres de los medios estan entre etiquetas em por lo tanto es lo que se debe buscar
            etiqueta_em=etiqueta_p.find_all('em')
            #Se hace un ciclo for para iterar por cada etiqueta encontrada y guardarla en una lista
            #Se hace de esta manera porque puede ser que un reportero trabaje para mas de un medio
            for etiqueta in etiqueta_em:
                auxiliar.append(etiqueta.text)
            medios.append(auxiliar[:])
            auxiliar.clear()

        elif negro.text not in posibles_pant:
            participant.append(negro.text)

    #Participantes de conferencia
    participantes=[]
    for negro in negritas:
        participantes.append(negro.text)

    #Imagenes
    #Obtenemos primero el elemento en el cual se guarda la imagen principal de la pagina
    imagenes=soup.find_all('img')
    #Pasamos los datos relevantes de las imagenes a la lista imagenes
    lista_imagenes = []
    auxiliar = []
    for i in range(len(imagenes)):
        auxiliar.append(imagenes[i]['src'])
        try:
            if imagenes[i]["alt"] == "":
                textoalterno = imagenes[i]['src'].split('/')
                auxiliar.append(textoalterno[-1])
            else:
                auxiliar.append(imagenes[i]["alt"])
        except:
            textoalterno = imagenes[i]['src'].split('/')
            auxiliar.append(textoalterno[-1])
        lista_imagenes.append(auxiliar[:])
        auxiliar.clear()

    #Articulo
    articulo=soup.find('article')

    #Audios
    audio=articulo.find_all('audio')
    #datos relevantes del audio
    lista_audio=[]
    auxiliar=[]
    for i in range(len(audio)):
        try:
            auxiliar.append(audio[i]['src'])
        except:
            continue
        try:
            if audio[i]['alt'] == '':
                textoalterno=audio[i]['src'].split('/')
                auxiliar.append(textoalterno[-1])
            else:
                auxiliar.append(audio[i]['alt'])
        except:
            textoalterno=audio[i]['src'].split('/')
            auxiliar.append(textoalterno[-1])
    lista_audio.append(auxiliar[:])
    auxiliar.clear()

    #Videos
    video=articulo.find_all('iframe')
    #Datos relevantes del video
    lista_video=[]
    auxiliar=[]
    for i in range(len(video)):
        try:
            auxiliar.append(video[i]['src'])
        except:
            continue
        try:
            if video[i]['title'] == '':
                textoalterno=video[i]['src'].split('/')
                auxiliar.append(textoalterno[-1])
            else:
                auxiliar.append(video[i]['title'])
        except:
            auxiliar.append('Sin Titulo')
              #textoalterno=video[i]['src'].split('/')
              #auxiliar.append(textoalterno[-1])
    lista_video.append(auxiliar[:])
    auxiliar.clear()

    lineastexto=texto.find_all('p')
    organizaciones=[]
    personas=[]
    localizaciones=[]
    for indice,linea in enumerate(lineastexto):
        doc = nlp(linea.text)
        for ent in doc.ents:
           if ent.label_ == 'ORG':
               organizaciones.append(ent.text)
           elif ent.label_ == 'PER':
               personas.append(ent.text)
           elif ent.label_ == 'LOC':
               localizaciones.append(ent.text)

    return titulo, fecha3, sub, lista_etiquetas, texto,entrevistadores,medios,lista_imagenes,organizaciones,personas,\
           localizaciones,lista_audio,lista_video,categoria,participant


#Modulo de limpieza secundaria de listas
def limpieza(lista):
    elementoseliminar=[]
    for indice,i in enumerate(lista):
        expresion=lista[indice]+r'\W'
        prueba=re.compile(expresion)
        for index,y in enumerate(lista):
            if index!=indice:
                if prueba.match(lista[index]):
                    elementoseliminar.append(index)
        for numero in elementoseliminar:
            try:
                lista.pop(numero)
            except:
                pass
        elementoseliminar.clear()

#Modulo que imprime todos los elementos encontrados
def impresion():
    #Area de impresion de resultados
    print('Titulo de la nota:\n',titulo,'\n')

    print('Fecha de la nota:\n',fecha3,'\n')

    print('Subtitulo de la nota:\n',sub,'\n')

    print('Categoria es: ', categoria)
    print()

    print('Participantes')
    for p in participant_nombre:
        print(p)
    print()

    print('Etiquetas:')
    for tag in lista_etiquetas:
       print(f'{tag}')
    print()

    print('Entrevistadores:')
    print(entrevistadores)
    print()

    print('Medios:')
    print(medios)
    print()

    print('Links a las imagenes')
    for i in lista_imagenes:
        print(i[0])
    print()

    print('Organizaciones limpias')
    print(organizaciones2[:])
    print(len(organizaciones2))
    print()

    print('Personas limpia')
    print(personas2[:])
    print(len(personas2[:]))
    print()

    print('Localizaciones limpias')
    print(localizaciones2[:])
    print(len(localizaciones2))
    print()

    print('Audio')
    for i in lista_audio:
        try:
            print(i[0])
        except:
            print('No hay audio')
    print('Video')
    for i in lista_video:
        try:
            print(i[0],'\n',i[1])
        except:
            print('No hay video')

    print('Texto completo:')
    print(texto.text)


def verificacion():
    #Seccion de Verificacion
    #En esta seccion se consulta la base de datos para no agregar registros duplicados
    mycursor=db.cursor()

    #Verificacion de etiquetas
    etiquetas_actuales=[]#Esta lista contendra las etiquetas que ya se tienen en la base de datos
    mycursor.execute('SELECT etiqueta FROM etiquetas')
    for x in mycursor:
        etiquetas_actuales.append(x[0])
    etiquetas_agregacion=[]#Esta lista contendra las etiquetas que sea agregaran a la base de datos
    for i in range(len(lista_etiquetas)):#Este ciclo for compara las listas, si hay una etiqueta que no este en la base de datos
        if lista_etiquetas[i] not in etiquetas_actuales:#entonces se agregara
            etiquetas_agregacion.append(lista_etiquetas[i])

    #Verificar subtitulo
    subtituloactual=[]
    mycursor.execute('SELECT subtitulo FROM subtitulo')
    for x in mycursor:
        subtituloactual.append(x[0])
    subtituloagregacion=[]
    if sub[1] not in subtituloactual:
        subtituloagregacion.append(sub)


    #Verificar participantes
    part_actuales=[]
    mycursor.execute('SELECT nombre FROM participantes')
    for x in mycursor:
        part_actuales.append(x[0])
    part_agregacion=[]
    aux=[]#lista auxiliar
    for i in range(len(participant_nombre)):
        if participant_nombre[i][0] not in part_actuales:
            if len(participant_nombre[i][0]) <= 50:#solamente se aceptaran nombres menores de 50 caracteres
                aux.append(participant_nombre[i][0])
                aux.append(participant_nombre[i][1])
                part_agregacion.append(aux[:])
                aux.clear()

    #Verificar categoria
    cat_actuales=[]
    mycursor.execute('SELECT cat FROM categoria')
    for x in mycursor:
        cat_actuales.append(x[0])
    cat_agregacion=[]
    if categoria not in cat_actuales:
        cat_agregacion.append(categoria)

    #Verificar periodistas
    periodistas_actuales=[]#Lista donde se guardaran los periodistas que ya se encuentran en la base de datos
    mycursor.execute('SELECT nombre from periodistas')
    for x in mycursor:
        periodistas_actuales.append(x[0])
    periodistas_agregacion=[]#Aqui se guardaran los periodistas nuevos que no estan en la base de datos
    for i in range(len(entrevistadores)):
        if entrevistadores[i] not in periodistas_actuales:
            periodistas_agregacion.append(entrevistadores[i])

    #Verificar Imagenes
    imagenes_actuales=[]
    mycursor.execute('SELECT url FROM multimedia')
    for x in mycursor:
        imagenes_actuales.append(x[0])
    imagenes_agregacion=[]#Aqui se guardaran las imagenes nuevas que no estan en la base de datos
    for i in range(len(lista_imagenes)):#Cada elemento de la lista_imagenes es una lista de dos elementos,
        try:
            if lista_imagenes[i][0] not in imagenes_actuales:#[i][0] es la url de la imagen, [i][1] es el texto alternativo
                imagenes_agregacion.append(lista_imagenes[i])#Es necesario comparar las url
        except:
            continue

    #Verificar videos
    videos_agregacion=[]
    for i in range(len(lista_video)):
        try:
            if lista_video[i][0] not in imagenes_actuales:
                videos_agregacion.append(lista_video[i])
        except:
            continue

    #Verificar audios
    audio_agregacion=[]
    for i in range(len(lista_audio)):
        try:
            if lista_audio[i][0] not in imagenes_actuales:
                audio_agregacion.append(lista_audio[i])
        except:
            continue

    #Verificar organizaciones
    org_actuales=[]
    mycursor.execute('SELECT nombre FROM entidades WHERE rol="ORG"')
    for x in mycursor:
        org_actuales.append(x[0])
    org_agregacion=[]
    for i in range(len(organizaciones2)):
        if organizaciones2[i] not in org_actuales:
            org_agregacion.append(organizaciones2[i])

    #Verificar personas
    personas_actuales = []
    mycursor.execute('SELECT nombre FROM entidades WHERE rol="PER"')
    for x in mycursor:
        personas_actuales.append(x[0])
    personas_agregacion = []
    for i in range(len(personas2)):
        if personas2[i] not in personas_actuales:
            personas_agregacion.append(personas2[i])

    #Verificar localizaciones
    loc_actuales = []
    mycursor.execute('SELECT nombre FROM entidades WHERE rol="LOC"')
    for x in mycursor:
        loc_actuales.append(x[0])
    loc_agregacion = []
    for i in range(len(localizaciones2)):
        if localizaciones2[i] not in loc_actuales:
            loc_agregacion.append(localizaciones2[i])

    #Verificar Medios
    medios_actuales=[]
    mycursor.execute('SELECT nombre FROM medios')
    for x in mycursor:
        medios_actuales.append(x[0])
    medios_agregacion=[]
    for i in range(len(medios)):
        for y in range(len(medios[i])):
            if medios[i][y] not in medios_actuales:
                medios_agregacion.append(medios[i][y])
    mycursor.close()

    #Retornamos valores para su uso en otros modulos
    return etiquetas_agregacion,periodistas_agregacion,medios_agregacion,imagenes_agregacion,org_agregacion,\
           personas_agregacion,loc_agregacion,audio_agregacion,videos_agregacion,subtituloagregacion,\
           cat_agregacion,part_agregacion

def agregar_tablas():
    #Creamos el cursor
    mycursor=db.cursor()

    # Ingreso de registros a la base de datos comenzando con tabla conferencias
    # Agregar registro a tabla conferencias
    mycursor.execute('INSERT INTO conferencias (titulo,fecha,texto,url) VALUES (%s,%s,%s,%s)',
                     (titulo, fecha3,texto.text,url1))

    #Agregar valores a tabla subtitulo
    for subt in subtituloagregacion:
        mycursor.execute('INSERT INTO subtitulo (subtitulo,año) VALUES (%s,%s)',(subt[1],int(subt[0])))

    #Agregar valores a tabla categoria
    for c in cat_agregacion:
        mycursor.execute('INSERT INTO categoria (cat) VALUES (%s)',(c,))

    #Agregar valores a tabla participantes
    for part in part_agregacion:
        mycursor.execute('INSERT INTO participantes (nombre,puesto) VALUES (%s,%s)',(part[0],part[1]))

    # Agregar etiquetas a la tabla etiquetas
    for etiquetan in etiquetas_agregacion:
        mycursor.execute('INSERT INTO etiquetas (etiqueta) VALUES (%s)', (etiquetan,))

    # Agregar periodistas
    for periodista in periodistas_agregacion:
        if len(periodista) <= 50:
            mycursor.execute('INSERT INTO periodistas (nombre) VALUES (%s)', (periodista,))

    #Agregar medios
    for medio in medios_agregacion:
        mycursor.execute('INSERT INTO medios (nombre) VALUES (%s)',(medio,))

    #Agregar Imagenes
    #Obtenemos el id de la conferencia actual, llevando a cabo la siguiente consulta
    mycursor.execute(f'SELECT id FROM conferencias WHERE titulo="{titulo}" AND fecha="{fecha3}"')
    # Ahora mycursor debe tener el id de la conferencia actual, se guardara en una variable
    for x in mycursor:
        idconferencia=x[0]#idconferencia contiene el id de la conferencia, es necesario iterar en mycursor para obtener el valor
        # no copiamos directamente los valores de x debido a que retorna una tupla
    #Agregamos valores a la tabla
    for imagen in imagenes_agregacion:
        mycursor.execute('INSERT INTO multimedia (textoalt,url,tipo,id_conferencia) VALUES (%s,%s,%s,%s)',
                         (imagen[1], imagen[0],'imagen',idconferencia))
    #Agregamos videos a la tabla multimedia
    for vid in video_agregacion:
        mycursor.execute('INSERT INTO multimedia (textoalt,url,tipo,id_conferencia) VALUES (%s,%s,%s,%s)',
                         (vid[1], vid[0],'video',idconferencia))
    #Agregamos audios a la tabla multimedia
    for audi in audio_agregacion:
        mycursor.execute('INSERT INTO multimedia (textoalt,url,tipo,id_conferencia) VALUES (%s,%s,%s,%s)',
                         (audi[1], audi[0],'audio',idconferencia))

    # Agregar entidades
    for organizacion in org_agregacion:
        mycursor.execute('INSERT INTO entidades (nombre,rol) VALUES (%s,%s)',(organizacion,'ORG'))
    for persona in personas_agregacion:
        mycursor.execute('INSERT INTO entidades (nombre,rol) VALUES (%s,%s)',(persona,'PER'))
    for localizacion in loc_agregacion:
        mycursor.execute('INSERT INTO entidades (nombre,rol) VALUES (%s,%s)',(localizacion,'LOC'))
    db.commit()
    mycursor.close()
    return idconferencia

#El modulo agregar_relaciones se encarga de agregar registros en las tablas que sirven como relacion para el resto de
#tablas, para trabajar necesitan verificar los ids de los registros que ingresaran para enlazar correctamente los datos
def agregar_relaciones():
    #Creamos el cursor
    mycursor=db.cursor()

    # Agregar valores a la tabla con_etiquetas la cual tiene la relacion de las etiquetas utilizadas en la nota
    # El id de la conferencia actual ya se encuentra en la variable idconferencia

    #Verificar id de los subtitulos
    mycursor.execute(f'SELECT id_sub FROM subtitulo WHERE subtitulo="{sub[1]}"')
    for x in mycursor:
        id_subtitulo=x[0]

    #Verificar id de la categoria
    mycursor.execute(f'SELECT id_cat FROM categoria WHERE cat="{categoria}"')
    for x in mycursor:
        id_categoria = x[0]

    #Verificar id participantes
    id_participantes=[]
    for i in participant_nombre:
        mycursor.execute(f'SELECT id_part FROM participantes WHERE nombre="{i[0]}"')
        for x in mycursor:
            id_participantes.append(x[0])

    # Verificar id de las etiquetas
    id_etiquetas = []  # Se verifica con la lista lista_etiquetas porque contiene todas las etiquetas que aparecen en la nota
    for i in lista_etiquetas:  # independientemente de si son nuevas o no
        mycursor.execute(f'SELECT id_etiquetas FROM etiquetas WHERE etiqueta="{i}"')
        for x in mycursor:
            id_etiquetas.append(x[0])

    #Verificar id de los periodistas
    id_periodistas=[]
    for i in entrevistadores:
        mycursor.execute(f'SELECT id_periodista FROM periodistas WHERE nombre="{i}"')
        for x in mycursor:
            id_periodistas.append(x[0])

    #Verificar ids de los medios
    id_medios=[]
    for i in medios:
        mycursor.execute(f'SELECT id_medio FROM medios WHERE nombre="{i}"')
        for x in mycursor:
            id_medios.append(x[0])

    #Verificar ids de los medios
    #Medios es una lista de listas, por tanto se trata diferente
    id_medios=[]
    id_medios_correspondencia=[]#En esta lista se guardaran los ids de los medios, en una lista de listas, donde cada
    #lista corresponde a los medios a los que pertenece cada periodista, en el caso de que el periodista pertenezca a
    #mas de un medio
    auxiliar1=[]
    for medio in medios:
        for submedio in medio:
            mycursor.execute(f'SELECT id_medio FROM medios WHERE nombre="{submedio}"')
            for x in mycursor:
                id_medios.append(x[0])
                auxiliar1.append(x[0])
        id_medios_correspondencia.append(auxiliar1[:])
        auxiliar1.clear()

    #Verificar id de las entidades
    id_entidades=[]
    for org in organizaciones2:
        mycursor.execute(f'SELECT id_entidad FROM entidades WHERE nombre="{org}"')
        for x in mycursor:
            id_entidades.append(x[0])
    for per in personas2:
        mycursor.execute(f'SELECT id_entidad FROM entidades WHERE nombre="{per}"')
        for x in mycursor:
            id_entidades.append(x[0])
    for loc in localizaciones2:
        mycursor.execute(f'SELECT id_entidad FROM entidades WHERE nombre="{loc}"')
        for x in mycursor:
            id_entidades.append(x[0])

    #Verificar tuplas existentes en medios_periodistas
    id_mediosperiodistas=[]#Lista de listas que contendra las tuplas ya existentes en la tabla
    auxiliar=[]
    mycursor.execute('SELECT id_periodista, id_medio FROM medios_periodistas')
    for x in mycursor:
        auxiliar.append(x[0])
        auxiliar.append(x[1])
        id_mediosperiodistas.append(auxiliar[:])
        auxiliar.clear()
    id_medios_periodistas_actuales=[]#Lista de listas que contendra las tuplas que hay en esta conferencia
    auxiliar2=[]
    #Formulacion de tuplas para agregar a la lista medios_periodistas
    #id_periodistas contiene los ids de todos los periodistas que ya estan en base de datos
    #id_medios_correspondencia contiene los id de todos los medios que ya estan en la base de datos, pero organizados
    #en listas, en donde cada lista corresponde a un periodista, asi el indice 0 de la lista contiene el id del
    #periodista y en la otra lista el indice 0 tiene una lista de todos los ids de los medios para los cuales trabaja
    for indice,idp in enumerate(id_periodistas):
        try:
            for idm in id_medios_correspondencia[indice]:
                auxiliar2.append(idp)
                auxiliar2.append(idm)
                id_medios_periodistas_actuales.append(auxiliar2[:])
                auxiliar2.clear()
        except IndexError:
            continue
    #Comparamos id_medios_periodistas_actuales contra id_medios_periodistas
    id_mediosperiodistas_agregacion=[]
    try:
        for i in id_medios_periodistas_actuales:
            if i not in id_mediosperiodistas:
                id_mediosperiodistas_agregacion.append(i)
    except:
        pass


    # Ya que tenemos los ids procedemos con llenar las tablas relacionales
    #LLenado de con_etiquetas
    for netiqueta in id_etiquetas:
        mycursor.execute('INSERT INTO con_etiquetas (id_con,id_et) VALUES (%s,%s)',(idconferencia, netiqueta))
    #Llenado de asistencia_conferencia
    for id in id_periodistas:
        mycursor.execute('INSERT INTO asistencia_conferencia (id_conferencia,id_periodista) VALUES (%s,%s)',(idconferencia,id))
    #Llenado de medios_conferencia
    for id in id_medios:
        mycursor.execute('INSERT INTO medios_conferencia (id_conferencia,id_medios) VALUES (%s,%s)',(idconferencia, id))
    #Llenado de entidades_conferencias
    for id in id_entidades:
        mycursor.execute('INSERT INTO entidades_conferencias (id_entidad,id_conferencia) VALUES (%s,%s)',(id,idconferencia))
    #Llenado de medios_periodistas
    for id in id_mediosperiodistas_agregacion:
        mycursor.execute('INSERT INTO medios_periodistas (id_periodista,id_medio) VALUES (%s,%s)',(id[0],id[1]))
    #Llenado de sub_con
    mycursor.execute('INSERT INTO sub_con (id_con,id_sub) VALUES (%s,%s)',(idconferencia,id_subtitulo))
    #Llenado de cat_con
    mycursor.execute('INSERT INTO cat_con (id_con,id_cat) VALUES (%s,%s)', (idconferencia, id_categoria))
    #Llenado de pat_conf
    for id in id_participantes:
        mycursor.execute('INSERT INTO pat_conf (id_con,id_part) VALUES (%s,%s)',(idconferencia,id))

    db.commit()
    mycursor.close()


#Ejecucion del loop de la aplicacion
#Direccion de la pagina de la cual obtendremos los links
tiempo1=time.time()
contador=0
for hub in range(1,256):#256
    url=f'https://lopezobrador.org.mx/transcripciones/page/{hub}'
    pagina=requests.get(url)
    sopa=BeautifulSoup(pagina.content,'html.parser')
    #buscamos links
    links=sopa.find_all('h2')
    print('Pagina',hub)
    print('Estimacion de links en pagina',len(links))
    for indecs,link in enumerate(links):
        print('Pagina',hub)
        print('Ejecucion',indecs+1)
        url1=link.a['href']
        page=requests.get(url1)
        print(url1)
        soup=BeautifulSoup(page.content, 'html.parser')

        #Ejecucion del modulo de busqueda
        titulo,fecha3,sub,lista_etiquetas,texto,entrevistadores,medios,lista_imagenes,organizaciones,personas,\
        localizaciones,lista_audio,lista_video,categoria,participant=busqueda()

        #Eliminamos duplicados de la lista con un ordereddict
        organizaciones2=list(OrderedDict.fromkeys(organizaciones))
        personas2=list(OrderedDict.fromkeys(personas))
        localizaciones2=list(OrderedDict.fromkeys(localizaciones))
        participant2=list(OrderedDict.fromkeys(participant))

        #Separamos nombre de puesto para los participantes del gobierno
        participant_nombre=[]
        for p in participant2:
            if ',' in p:
                aux=p.split(',')
                participant_nombre.append(aux[:])
            elif ':' in p:
                aux=p.split(':')
                participant_nombre.append(aux[:])

        #Segunda eliminacion de duplicados
        #Buscamos nombres duplicados y guardamos el sub indice donde estan
        actuales=[]
        repeticiones=[]
        ides=[]
        for i in range(len(participant_nombre)):
            if participant_nombre[i][0] in actuales:
                repeticiones.append(participant_nombre[i][0])
                ides.append(i)
            else:
                actuales.append(participant_nombre[i][0])
        #Eliminamos los duplicados de la lista
        #Ordenamos subindices de mayor a menor
        ides.sort(reverse=True)
        for i in range(len(ides)):
            participant_nombre.pop(ides[i])



        #eliminamos elementos muy similares con regex
        try:
            limpieza(organizaciones2)
        except:
            pass
        try:
            limpieza(personas2)
        except:
            pass
        try:
            limpieza(localizaciones2)
        except:
            pass

        #Ejecucion de modulo impresion
        impresion()

        #Ejecucion del modulo de verificacion
        etiquetas_agregacion,periodistas_agregacion,medios_agregacion,imagenes_agregacion,org_agregacion,\
        personas_agregacion,loc_agregacion,audio_agregacion,video_agregacion,subtituloagregacion,\
        cat_agregacion,part_agregacion=verificacion()

        #Ejecucion del modulo agregar tablas
        idconferencia=agregar_tablas()

        #Ejecucion del modulo agregar relaciones
        agregar_relaciones()

        #Espera para no activar alarmas
        print('Ejecucion finalizada')
        print('Esperando 3 segundos')
        print()
        contador=contador+1
        time.sleep(3)

tiempo2=time.time()
tiempo3=tiempo2-tiempo1
tperdido=contador*3
tneto=tiempo3-tperdido
print('Tiempo total transcurrido: ',tiempo3)
print('Total de ejecuciones realizadas: ',contador)
print('Tiempo perdido en esperas: ',tperdido)
print('Tiempo neto de ejecucion: ',tneto)