---
titulo: BDNS e IATI cuentan el mismo dinero y nunca cuadran
descripcion: Dos registros públicos recogen las mismas subvenciones de la cooperación española y dan cifras distintas. Por qué ocurre y qué se puede hacer con ello.
fecha: 2026-09-11
resumen: Un mismo euro de cooperación española puede estar anotado en dos registros oficiales a la vez, con importes distintos, en momentos distintos y con unidades de medida distintas. Esto es lo que aparece al compararlos uno contra otro.
---

Cuando la Agencia Española de Cooperación Internacional para el Desarrollo (AECID) concede dinero a un proyecto, ese dinero termina anotado en dos sitios distintos. Uno es la Base de Datos Nacional de Subvenciones, la BDNS: el registro español donde toda administración pública tiene que apuntar las subvenciones que concede, por mandato de la Ley General de Subvenciones. El otro es IATI, la Iniciativa Internacional para la Transparencia de la Ayuda, un estándar internacional en el que los donantes publican sus actividades de cooperación con un formato común.

Los dos registros son públicos, los dos son gratuitos y los dos hablan del mismo dinero. Y no cuadran. Nunca. Esta web se construye sobre las dos fuentes, así que la discrepancia no es una curiosidad: es un problema de trabajo diario. Lo que sigue es lo que aparece al ponerlas una al lado de la otra.

## Dos registros, dos propósitos

La BDNS es un censo de subvenciones concedidas en España, sin importar para qué sean: becas, ayudas agrarias, subvenciones municipales a un club deportivo o cooperación internacional. Es enorme. En una consulta a su API pública, el catálogo completo rondaba los 29,5 millones de concesiones. AECID aparece ahí como un organismo estatal más: sus filas llevan el nivel administrativo "ESTADO" y, como organismo concedente, el nombre completo de la agencia.

IATI es otra cosa. Es un estándar internacional pensado para que la ayuda al desarrollo de distintos países se pueda comparar entre sí. Cada organismo que publica tiene un código; el de AECID es XM-DAC-50-21. Cada actividad publicada declara un país receptor, un sector, unas fechas y unos importes.

Uno es un registro administrativo español de subvenciones. El otro es un registro internacional de ayuda al desarrollo. Que el mismo euro aparezca en los dos no responde a ningún diseño conjunto: es una coincidencia de propósitos. Y se nota en todo lo demás.

## La unidad de medida no es la misma

En la BDNS la unidad es la concesión: un beneficiario, un importe, una fecha, dentro de una convocatoria. En IATI la unidad es la actividad: un proyecto con identificador propio, con uno o varios países receptores.

No hay correspondencia de uno a uno. Una convocatoria grande —las de acción humanitaria son el ejemplo típico— genera de golpe decenas de concesiones a decenas de beneficiarios, y en IATI eso puede aparecer como una sola actividad. Por eso, cuando esta web compara los dos registros para saber qué ya está publicado y qué todavía no, la comparación se hace al nivel de la convocatoria y no de la concesión: si una convocatoria ya tiene actividad en IATI, se dan por publicadas todas sus concesiones. Es una decisión deliberadamente conservadora. Prefiere esconder alguna concesión que todavía no tenga su propia actividad antes que arriesgarse a contar dos veces el mismo dinero.

## El mismo proyecto, dos importes

Aquí está el detalle que más despista. Comparando a mano proyectos concretos contra la API pública de la BDNS aparecieron dos casos que explican casi todo:

En una convocatoria tramitada como concesión directa, el presupuesto que declara la BDNS (139.312,92 €) coincide prácticamente al céntimo con el importe que la actividad declara en IATI (139.312 €). Hay un solo beneficiario y todo el dinero de la convocatoria es su proyecto.

En una convocatoria de concurrencia competitiva, el presupuesto de la BDNS es un millón de euros redondo y el importe del proyecto en IATI es 993.291 €. No es un error de nadie: el millón es el tamaño del fondo al que varias entidades concurren, y el proyecto solo se lleva su porción.

Es decir, el mismo campo puede significar "todo el pastel" o "el tamaño del pastel del que este proyecto es un trozo", según cómo se tramitara la convocatoria. Por eso esta web muestra en cada tarjeta de proyecto el tipo de convocatoria tal cual lo devuelve la BDNS, cuando lo conoce, y no muestra el presupuesto de la convocatoria junto al importe del proyecto: enseñar las dos cifras sin contexto induce exactamente al malentendido que las hace incomparables.

## La BDNS llega antes

La obligación de registrar una concesión en la BDNS es administrativa y rápida. La publicación en IATI va detrás.

Un caso verificado: una concesión a una fundación costarricense para un proyecto forestal, concedida el 21 de julio de 2026 y registrada en la BDNS el 19 de agosto de 2026. El 1 de septiembre seguía sin aparecer en los datos de IATI, que se habían descargado el día anterior.

Una medida más amplia, de esa misma descarga del 31 de agosto de 2026: la actividad más reciente publicada por AECID en IATI tenía fecha de inicio del 21 de abril. Conviene leer ese número con cuidado, porque no es exactamente un retraso de publicación —la fecha que se compara es la de inicio del proyecto, no la de su publicación—, pero da la medida del hueco: a finales de agosto, lo más nuevo que contaba IATI había empezado en abril.

## El puente entre ambos registros es un enlace en una página web

Esta es la parte que menos se espera uno. El XML que AECID publica en IATI no contiene el número de convocatoria de la BDNS. No hay un identificador alternativo, no hay un enlace a documento. El único sitio donde ese número aparece es la ficha pública de la propia actividad en el portal de datos de AECID, en su sección de enlaces.

O sea: la única pasarela entre dos registros públicos del mismo dinero es un enlace colocado en el pie de una página web. Una vez se sigue ese enlace, la correspondencia sí es exacta —se comprobó contra la API de la BDNS que el número que aparece al final de esa URL es literalmente el campo "número de convocatoria" de cada concesión—, pero depende por completo de que ese formato de URL no cambie. Si cambia, la correspondencia deja de funcionar sin avisar.

## Qué significa para quien intenta sumar

La conclusión práctica es corta: no sume las dos fuentes. Dan cifras distintas porque cuentan unidades distintas, en momentos distintos y con reglas distintas sobre qué es "el importe".

Lo que sí se puede hacer, y es lo que hace esta web, es usar la BDNS como señal adelantada y mantenerla separada. Las concesiones de AECID que ya están en la BDNS y todavía no en IATI se muestran en una línea aparte, marcadas como preliminares, y nunca se suman al total comprometido con un país. Entre otras razones porque la BDNS no declara en ningún sitio a qué país va el dinero, pero esa es otra historia.

Ninguno de los dos registros miente. Miden cosas distintas y las llaman casi igual.
