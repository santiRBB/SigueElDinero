---
titulo: Lo que estos datos no cuentan
descripcion: Los huecos de la cooperación española publicada: nada anterior a 2024, el dinero sin país, el dinero que no está en euros y los organismos que no publican.
fecha: 2026-09-17
resumen: Un inventario honesto de lo que falta en esta web y por qué falta. Casi todos los huecos no son errores de carga: son campos que la fuente no rellena o decisiones deliberadas de no adivinar.
---

Una web hecha de datos oficiales da una impresión de completitud que casi nunca está justificada. Este artículo es el inventario de lo que falta. Algunos huecos son decisiones de esta web, y se explican; otros vienen de la fuente y no hay forma de taparlos desde aquí.

## No hay nada anterior a 2024

Es el hueco más grande y el más fácil de pasar por alto. AECID no tiene publicada en IATI ninguna actividad con fecha de inicio anterior al 1 de enero de 2024.

Eso significa que esta web no es una historia de la cooperación española. Es una ventana que se abre en 2024. Cualquier comparación con años anteriores, cualquier frase del tipo "España ha destinado a este país tanto dinero", es falsa si se apoya solo en lo que aquí se ve.

El contraste con la otra fuente lo deja claro: en la Base de Datos Nacional de Subvenciones (BDNS), el registro español donde toda administración pública anota las subvenciones que concede, hay concesiones de AECID desde 2022. Existen, están registradas y son públicas. Simplemente no tienen actividad equivalente publicada en IATI, y probablemente no vayan a tenerla nunca: ese periodo queda fuera de lo que AECID ha publicado en el estándar.

Esto tiene una consecuencia práctica que conviene decir en voz alta. Esta web marca como "preliminares" las concesiones que ya están en la BDNS y todavía no en IATI, pero la palabra engaña: la mayor parte de ese importe corresponde a concesiones anteriores a 2024, que no están pendientes de publicarse, sino fuera de la ventana publicada.

## El dinero sin país no aparece en el mapa

Para que un proyecto salga en el mapa tiene que tener un país receptor declarado. Y muchos no lo tienen.

La ingesta de datos separa explícitamente esas actividades: las que no declaran país se apartan a un fichero propio y no entran en la tabla que alimenta el mapa, las fichas de país ni los totales. No es un descarte silencioso, pero es un descarte.

Qué suele haber ahí: contribuciones a organismos multilaterales. Cuando España aporta a un fondo global —el Fondo Global de lucha contra el sida, GAVI para vacunación— ese dinero es cooperación española de pleno derecho, pero no tiene un país receptor, porque el fondo decide después dónde se gasta. En el mapa de esta web ese dinero no está en ninguna parte.

Hay una variante más sutil. El estándar admite en el campo de país receptor códigos que no son países, sino regiones. Cuando el código que llega no corresponde a ningún país reconocido, la fila se guarda igualmente para no perder el dato, pero se queda sin código de país estándar, y todas las consultas que alimentan el mapa y las fichas filtran precisamente por ese código. El dinero está en la base y no está en la pantalla.

## El dinero que no está en euros

Este hueco es pequeño en apariencia y desagradable en la práctica. Cada actividad de IATI declara sus transacciones con una moneda. La ingesta suma a euros únicamente las transacciones que vienen en euros. Las que vienen en otra moneda se anotan aparte, por moneda, sin convertir: no se inventa un tipo de cambio.

Hasta ahí, es una decisión prudente y correcta. La consecuencia es la que hay que tener presente: ese apartado en otras monedas no llega a la base de datos que alimenta la web. Una actividad declarada íntegramente en dólares contribuye cero euros a los totales que aquí se muestran, aunque exista, tenga país y tenga sector.

## Las concesiones cuyo país no se puede saber

En la BDNS no hay campo de país. El país solo se puede intentar leer del texto libre del título de la convocatoria, y la regla que usa esta web es deliberadamente estricta: si el texto menciona exactamente un país sin ambigüedad, se asigna; si menciona cero o más de uno, se queda sin país.

El resultado es que hay un importe real, de concesiones reales de AECID, que no aparece en la ficha de ningún país porque no se sabe con certeza a cuál asignarlo. Ese importe se muestra en la página "Sobre los datos", con el número de concesiones y con enlace a cada una en la BDNS, precisamente para que no desaparezca sin dejar rastro. Es el precio de no adivinar: preferir un hueco visible a un país inventado.

## Esta web no es "España", es AECID

La ingesta de IATI descarga las actividades de un único organismo publicador: AECID. Otros organismos españoles que publiquen en el mismo estándar —comunidades autónomas, ayuntamientos, otros ministerios— no están aquí. Añadirlos es técnicamente trivial, basta con añadir su código de publicador a la lista, pero mientras no se haga, lo que se ve es la cooperación de la agencia, no la del país.

Por eso un país en gris en el mapa no significa que no reciba cooperación española. Significa que no hay actividades de AECID cargadas para ese país con los filtros que estén puestos en ese momento.

Hay una excepción que merece aviso propio: el mapa de comunidades autónomas de la ficha de España sale de la BDNS y son subvenciones públicas de cualquier tipo concedidas dentro de España, no cooperación internacional. Es un dato distinto, a otra escala, y no se suma a ningún total de cooperación.

## Nada de esto dice si el proyecto funcionó

El último hueco es el más importante y el que ninguna base de datos de estas va a tapar. Lo que se guarda de cada intervención es: un importe, un país, un sector, un organismo ejecutor, unas fechas y unos enlaces a la ficha oficial. Eso es todo.

No hay ningún campo sobre resultados. Ni sobre ejecución real frente a lo previsto, ni sobre si el proyecto terminó, ni sobre qué se consiguió con el dinero. Un proyecto de un millón de euros que salió perfecto y otro de un millón que se quedó a medias se ven exactamente igual en este mapa.

Seguir el dinero es el primer paso y no es el último. Esta web sirve para saber cuánto, a dónde y a través de quién. Para saber para qué sirvió hay que ir a la ficha original de cada proyecto, que está enlazada en todas partes por este mismo motivo.
