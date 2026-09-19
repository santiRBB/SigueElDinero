---
titulo: "Un proyecto, varios países: el problema del reparto"
descripcion: Cuando una actividad de cooperación cubre siete países con un solo importe, alguien tiene que decidir cuánto le toca a cada uno. Cómo se hace y cuándo es una estimación.
fecha: 2026-09-15
resumen: La cifra que esta web muestra para cada país no siempre sale de la fuente tal cual. A veces sale de un reparto declarado por AECID y a veces de un reparto asumido a partes iguales, que es una decisión de esta web y no un dato.
---

Hay una pregunta incómoda detrás de cualquier mapa de ayuda al desarrollo: ¿cuánto dinero le tocó a cada país? Parece una pregunta de sumar. No lo es.

Buena parte de la cooperación no se organiza país por país. Un programa forestal en Centroamérica, una contribución a un fondo regional, una convocatoria humanitaria que cubre varios destinos: son un solo proyecto, con un solo presupuesto, repartido entre varios sitios. Para colocar ese dinero en un mapa hay que partirlo. Y partirlo requiere información que a veces está y a veces no.

## Lo que IATI sí permite declarar

El estándar IATI, en el que AECID publica sus actividades, contempla el caso. Una actividad puede declarar varios países receptores y, junto a cada uno, un porcentaje. Ese porcentaje es la respuesta oficial a la pregunta: de este millón, el 40 % es para este país y el 25 % para aquel otro.

Cuando ese porcentaje está declarado, esta web lo usa tal cual. El importe que se asigna a cada país es el importe total de la actividad multiplicado por el porcentaje que declaró el propio organismo publicador. No hay estimación por medio, y la ficha del proyecto no lleva ninguna advertencia.

Hay un caso real que ilustra bien lo que esto permite: un programa de bosques en Mesoamérica, pagado a través de un único organismo intermediario, con un único identificador de actividad, pero con porcentajes explícitos repartidos entre Belice, Costa Rica, El Salvador, Guatemala, Honduras, México y Panamá. Siete países, un solo proyecto, un reparto declarado. Eso es exactamente lo que el estándar hace bien.

## Lo que hay que asumir cuando no se declara

El problema es que declarar el porcentaje es opcional. Una actividad puede nombrar cinco países receptores y no decir nada sobre cómo se reparte el dinero entre ellos.

Ahí hay tres opciones y ninguna es buena. La primera es descartar el proyecto: el mapa quedaría limpio pero incompleto, y desaparecerían justamente los programas regionales, que suelen ser de los más grandes. La segunda es asignarle el importe entero a cada país, que multiplicaría el total por el número de países. La tercera, que es la que aplica esta web, es repartir a partes iguales.

Si una actividad declara cuatro países sin porcentajes, cada uno recibe el 25 % del importe. Y esa fila queda marcada en la base de datos como reparto asumido, no declarado, para no fingir una precisión que la fuente no dio. En la ficha del proyecto aparece con la etiqueta "Reparto estimado entre países".

Conviene entender lo que eso significa. Imagine un proyecto de un millón de euros que cubre cuatro países y en el que, en la práctica, el 90 % del gasto ocurre en uno solo. Esta web mostraría 250.000 € en cada uno de los cuatro. El total global seguiría siendo correcto —un millón, ni más ni menos—, pero las cuatro cifras por país serían falsas a la vez. El reparto igualitario no es neutro: es una suposición concreta que, cuando falla, falla repartiendo hacia abajo el país grande y hacia arriba los pequeños.

Por eso la etiqueta importa más que el número. Si un proyecto grande de la ficha de un país lleva la marca de reparto estimado, la cifra de ese país está construida sobre una suposición, no sobre una declaración. Y merece una comprobación antes de citarla.

## Hay un caso en el que no hay ambigüedad

Cuando una actividad declara un solo país receptor y ningún porcentaje, se le asigna el 100 % y se marca como declarado, no como estimado. No es una suposición: con un único país, no hay reparto posible. La distinción parece menor, pero evita llenar el sitio de advertencias en proyectos que no tienen ningún problema.

## En la BDNS ni siquiera hay reparto

El otro registro que usa esta web, la Base de Datos Nacional de Subvenciones (BDNS), donde toda administración pública española anota las subvenciones que concede, es mucho peor en esto: no tiene campo de país. Ninguno. Una concesión es un beneficiario, un importe y una fecha; a dónde va ese dinero no se declara en ningún sitio estructurado.

Lo único que hay es el texto libre del título de la convocatoria, que a veces nombra el país —"EGIPTO 2026", "Convocatoria Instrumental NICARAGUA"— y a veces no lo nombra en absoluto. Esta web intenta leerlo, con una regla explícita: si el texto menciona exactamente un país reconocible, se le asigna ese país; si no menciona ninguno, o menciona más de uno, se queda sin país. Nunca se adivina.

Esa regla es más frágil de lo que parece, y cada salvaguarda que lleva viene de un error real observado contra datos de producción:

Hay que buscar por palabra completa y no por fragmento, porque "Cisjordania" contiene "Jordania" y no tienen nada que ver. Hay que quedarse con el nombre más largo que encaja en cada posición, porque si no "Guinea-Bisáu" cuenta como dos países a la vez —Guinea y Guinea-Bisáu— y la concesión se descarta por ambigua sin serlo.

Hay nombres de país que se han sacado de la lista a propósito, porque colisionan con nombres españoles corrientes: "España", porque una subvención doméstica a una coordinadora de ONG con "España" en el nombre resolvía a España como país receptor; "Granada", porque la Universidad de Granada resolvía al país caribeño; "Santa Lucía", porque Santa Lucía de Tirajana es un municipio de Gran Canaria.

Y hay una última trampa: las enumeraciones. Una concesión cuyo título es "Contribución voluntaria Marruecos, Sahel, América Latina" solo tiene un país reconocible, Marruecos, porque ni "Sahel" ni "América Latina" son países. Atribuirle a Marruecos el importe entero sería sencillamente incorrecto. La regla actual detecta que un término regional aparece pegado al país —a menos de veinte caracteres— y descarta la fila, mientras que sigue aceptando los casos en los que la región es parte del nombre del programa y el país real aparece mucho más lejos en el texto.

El resultado buscado es una cobertura baja con una precisión alta. Es mejor no saber a qué país fue una concesión que decir el país equivocado.

## Por qué las dos fuentes no se mezclan

Todo lo anterior explica una decisión que de otro modo parecería excesivamente prudente: el dinero que esta web ve en la BDNS y todavía no en IATI nunca se suma al total comprometido con un país. Se muestra en una línea aparte.

La razón es justamente el reparto. Una concesión de la BDNS es un importe único pagado a un intermediario, sin declaración de reparto de ningún tipo. Si el texto menciona un país, atribuirle el 100 % puede estar bien o puede ser un error del tamaño del proyecto entero —como habría pasado con el programa de Mesoamérica, que en la BDNS habría sido una sola línea y en IATI son siete países con porcentajes.

Una cifra por país no es una medición. Es una construcción, con reglas que se pueden mirar.
