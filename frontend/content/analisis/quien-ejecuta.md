---
titulo: Quién ejecuta la cooperación española
descripcion: AECID pone el dinero, pero casi nunca es quien está sobre el terreno. Qué dicen los datos sobre las entidades ejecutoras y qué no se puede saber con ellos.
fecha: 2026-09-09
resumen: El nombre de quien ejecuta un proyecto es uno de los campos más útiles de estos datos y uno de los más frágiles. Esto es lo que hay detrás de cada línea de entidad ejecutora en esta web.
---

Debajo del título de cada proyecto de esta web hay una línea pequeña con el nombre de una entidad. Es el organismo ejecutor, y es probablemente el campo más interesante de todos, porque responde a la pregunta que sigue naturalmente a "cuánto dinero": ¿en manos de quién acaba?

También es uno de los campos más frágiles. Merece la pena explicar por qué.

## AECID financia; ejecutar, ejecuta otro

En el estándar IATI, en el que AECID publica sus actividades, cada actividad puede declarar varios organismos participantes, y cada uno lleva un código que dice qué papel tiene en el proyecto. Uno de esos papeles es el de organismo ejecutor.

Esta web se queda con uno solo: el organismo cuyo papel declarado es el de ejecutor. Ese es el nombre que aparece en la tarjeta de cada proyecto.

La lectura correcta de ese nombre es: la entidad que, según lo que declaró AECID en el estándar, lleva a cabo el proyecto. No es necesariamente quien tiene el equipo sobre el terreno —una organización internacional puede subcontratar, una federación puede trabajar con socios locales— y de eso los datos no dicen nada.

## Si hay varios ejecutores, solo se guarda el primero

Aquí hay una simplificación que conviene conocer. El estándar permite declarar varios organismos con el papel de ejecutor en una misma actividad: consorcios, agrupaciones de ONG, proyectos con un socio en cada país.

La ingesta de datos de esta web toma el primero que encuentra con ese papel y descarta el resto. Así que un proyecto ejecutado por tres organizaciones aparece aquí con el nombre de una sola, y las otras dos no constan en ningún sitio.

Eso significa que contar proyectos por entidad ejecutora en esta web da un número a la baja para las entidades que suelen trabajar en consorcio, y no lo indica ninguna advertencia en pantalla. Es una limitación asumida al construir el sitio, y este párrafo es la advertencia.

## Y si no hay ninguno, no hay nada

Declarar los organismos participantes tampoco es obligatorio. Cuando una actividad no declara ningún ejecutor, la tarjeta del proyecto muestra "Organismo no especificado".

No es que el proyecto no tenga quien lo ejecute: es que en el fichero publicado ese dato no está. Es el mismo patrón que recorre todos estos datos —los huecos casi nunca son de carga, son campos que la fuente dejó vacíos.

## Dos formas de escribir el mismo nombre son dos organizaciones

Este es el problema técnico más serio del campo, y afecta a cualquiera que quiera hacer un ranking de entidades.

La base de datos de esta web identifica cada organismo por su nombre, tal cual viene escrito en el fichero. No por un identificador, no por un código fiscal: por la cadena de texto. Dos formas distintas de escribir la misma organización —con y sin siglas, con y sin "Fundación" delante, con una coma de más— crean dos organismos distintos, con sus proyectos repartidos entre ambos.

Y el buscador de proyectos funciona igual: busca el texto que se escriba dentro del nombre almacenado. Si una organización aparece con dos grafías, una búsqueda por una de ellas no encuentra los proyectos de la otra.

Por eso en esta web no hay, hoy, ningún ranking de entidades ejecutoras. Sería el listado más compartible del sitio y sería el más engañoso: mezclaría entidades reales con duplicados ortográficos, y no hay forma honesta de presentarlo sin una normalización de nombres que todavía no existe.

## La web tampoco clasifica por tipo de entidad

Otra cosa que no está: la distinción entre una ONG, una universidad, un organismo multilateral y una administración pública.

Esta web no guarda ninguna clasificación por tipo de entidad: todos los organismos ejecutores se almacenan con la misma etiqueta genérica. Quien quiera saber cuánto va a ONG frente a cuánto va a organismos internacionales tiene que leer los nombres uno a uno. Es una carencia conocida, no una decisión editorial.

## Por la otra puerta: quién cobra, según la BDNS

Hay una segunda fuente que dice algo distinto y complementario. En la Base de Datos Nacional de Subvenciones (BDNS), donde toda administración pública española anota las subvenciones que concede, cada concesión de AECID lleva el nombre del beneficiario: la entidad que efectivamente recibe el dinero.

Es un dato administrativo, no de cooperación, y por eso llega antes. En un caso verificado, una concesión a una fundación costarricense para un proyecto forestal, concedida el 21 de julio de 2026, estaba registrada en la BDNS el 19 de agosto y todavía no aparecía en IATI a comienzos de septiembre. Durante semanas, el único registro público donde ese dinero constaba, con el nombre de quien lo recibía, fue la BDNS.

Esta web muestra esas concesiones en la página "Sobre los datos", con beneficiario, importe, fecha y enlace directo a la ficha en la BDNS, precisamente para que se puedan mirar una a una.

## El tipo de convocatoria dice cómo se eligió

Y un último apunte, que es de los que cambian la lectura de una lista de entidades. Las subvenciones de la BDNS llevan un tipo de convocatoria, y esta web lo muestra en la tarjeta del proyecto cuando lo conoce.

Una concesión directa significa que el dinero se asignó a un beneficiario determinado. Una convocatoria de concurrencia competitiva significa que varias entidades concurrieron a un fondo común y se repartieron su presupuesto. Son dos formas muy distintas de llegar al mismo sitio, y explican por qué el importe de un proyecto a veces coincide con el presupuesto entero de la convocatoria y a veces es solo una parte.

Saber quién ejecuta es la mitad de la pregunta. La otra mitad —cómo llegó a ejecutarlo— está en el tipo de convocatoria, a un clic de distancia en cada tarjeta.
