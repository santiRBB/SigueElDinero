---
titulo: Qué es IATI y por qué la cooperación española se publica ahí
descripcion: El estándar internacional en el que AECID publica sus actividades de cooperación, qué obliga a declarar y qué deja en manos de cada organismo.
fecha: 2026-09-02
resumen: IATI es el formato común en el que los donantes del mundo publican su ayuda al desarrollo. Entender qué campos define, y cuáles son opcionales, explica casi todas las rarezas de los datos que se ven en esta web.
---

Casi todos los datos de cooperación internacional que hay en esta web vienen del mismo sitio: IATI, la Iniciativa Internacional para la Transparencia de la Ayuda. No es una base de datos ni una institución que audite a nadie. Es un formato.

La idea es sencilla y anterior a casi todos los portales de transparencia que conocemos. Si cada donante —países, agencias, fundaciones, bancos de desarrollo— publica lo que financia en un fichero con la misma estructura, con los mismos nombres de campo y los mismos códigos, entonces cualquiera puede juntar lo de todos y compararlo. Sin pedir permiso, sin firmar convenios y sin esperar a que alguien publique un informe anual.

## Qué es una actividad

La unidad de IATI es la actividad: lo que en lenguaje corriente llamaríamos un proyecto. Cada actividad tiene un identificador único y permanente, y dentro de ella se declara, entre otras cosas:

- El organismo que informa y su código de publicador. El de AECID es XM-DAC-50-21, y ese código es lo que permite pedir "todo lo que ha publicado la agencia española" sin ambigüedad.
- Un título y una descripción.
- El estado de la actividad: en ejecución, finalizada, cancelada.
- Fechas de inicio y fin, en dos versiones: las previstas y las reales.
- Uno o varios países receptores, cada uno con un porcentaje opcional del importe.
- Uno o varios sectores, con un vocabulario que dice qué clasificación se está usando; la habitual es la del Comité de Ayuda al Desarrollo de la OCDE.
- Los organismos participantes, cada uno con un papel: quién financia, quién acredita, quién ejecuta.
- Y las transacciones: movimientos de dinero, cada uno con su tipo (un compromiso, un desembolso) y su moneda.

Esa lista es la que explica la estructura de esta web. Cuando aquí se ve un importe con un país, un sector, un organismo ejecutor y unas fechas, eso no es una interpretación: es la actividad de IATI desmontada en sus campos.

## Cómo se obtienen los datos

No hace falta ningún permiso ni clave de acceso. Los datos de IATI se consultan desde servicios públicos que indexan lo que publica cada organismo, y esta web los descarga de uno de ellos, actividad por actividad.

De cada actividad se guarda además el XML original tal como venía, sin tocar. No es una manía de archivero: si mañana cambia la forma de interpretar un campo, o aparece un error de carga, se puede reprocesar desde la fuente exacta que se descargó ese día en lugar de volver a pedirla y arriesgarse a que haya cambiado por el camino.

AECID publica también, para cada actividad, una ficha en su propio portal de datos abiertos. Esa ficha es importante por una razón inesperada: es el único sitio donde aparece el enlace a la convocatoria correspondiente en la Base de Datos Nacional de Subvenciones, el registro español de subvenciones. En el fichero de IATI ese número no está.

## Lo que el estándar no garantiza

Aquí está la parte que explica la mayoría de los huecos que se encuentran mirando estos datos. IATI define qué campos existen. No obliga a que estén rellenos, ni verifica lo que se pone en ellos.

Tres ejemplos concretos, de los que más se notan:

**El nombre del sector.** Cada actividad puede declarar su sector con el código y también con su nombre en texto. Muchos organismos, AECID entre ellos, publican solo el código. Esta web resuelve ese código contra la lista oficial del estándar para no dejar el nombre vacío, y deja anotado de dónde salió el nombre en cada caso: del publicador o de la lista oficial. Es una diferencia pequeña que conviene poder auditar.

**El reparto entre países.** Una actividad puede nombrar varios países receptores y no decir qué porcentaje va a cada uno. El campo existe; rellenarlo es opcional. Cuando falta, cualquier cifra por país es una reconstrucción.

**El historial.** Nadie obliga a publicar retroactivamente. AECID no tiene publicada en IATI ninguna actividad con fecha de inicio anterior al 1 de enero de 2024, así que en el estándar no hay historia previa de su cooperación, por mucho que esa cooperación existiera y esté documentada en otros registros.

## Publicado no es lo mismo que legible

Que un dato esté publicado no significa que sea fácil de leer. Un fichero de IATI es XML, con códigos numéricos para casi todo: el país es un código de dos letras, el sector es un número de cinco cifras, el tipo de transacción es un dígito y el papel de cada organismo participante es otro dígito. Para una persona que quiera saber cuánto ha puesto España en un país concreto, eso es tan opaco como no publicar nada.

Esa distancia entre "está publicado" y "se puede consultar" es la razón de ser de esta web, y también de la sección de análisis en la que está leyendo esto. La traducción del estándar a lenguaje corriente tiene decisiones detrás, y esas decisiones cambian las cifras. Vale la pena que estén escritas.

## Qué mirar cuando se consulta un dato

Tres reflejos útiles con cualquier dato de IATI, aquí o en cualquier otro portal que lo use.

Primero, mirar si el importe es un compromiso o un desembolso, porque no significan lo mismo. Segundo, mirar si la cifra por país sale de un porcentaje declarado o de un reparto asumido. Y tercero, mirar el periodo cubierto antes de comparar años, porque un salto en las cifras puede ser un cambio en la cooperación o simplemente el punto en el que un organismo empezó a publicar.

Los tres tienen artículo propio en esta sección. El estándar no engaña a nadie: simplemente no se explica solo.
