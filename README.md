🖼️ Clasificador de Imágenes con IA Local
Herramienta en Python que organiza automáticamente miles de fotos en carpetas por contenido, usando un modelo de visión por IA que corre 100% en tu computador.
Sin APIs. Sin suscripciones. Sin costo. Tus fotos no salen de tu máquina.

¿Qué hace?

Recorre todas tus carpetas y subcarpetas buscando imágenes
Clasifica cada foto por contenido (paisajes, personas, comida, animales, etc.)
Las copia organizadas en carpetas por categoría
Muestra una ventana de progreso en tiempo real mientras trabaja
Permite revisar y corregir clasificaciones con clic derecho

¿Cómo funciona?
Usa ResNet50, una red neuronal entrenada en más de 1.2 millones de imágenes (ImageNet). El modelo reconoce el contenido visual de cada foto y la asigna a una categoría automáticamente. Todo corre localmente — no necesita internet después de la primera descarga del modelo.

Requisitos

Python 3.8 o superior
Las siguientes librerías:

bashpip install torch torchvision pillow

Tkinter viene incluido con Python en la mayoría de sistemas. Si no lo tienes: sudo apt install python3-tk (Linux) o reinstala Python marcando la opción Tcl/Tk (Windows).


Uso
bashpython clasificador_imagenes.py
Al ejecutarlo aparecerán dos ventanas de selección:

Carpeta raíz — elige la carpeta que contiene tus imágenes (buscará en todas las subcarpetas)
Carpeta de destino — elige dónde guardar las imágenes clasificadas

Luego el script trabaja solo. Puedes ver el progreso en tiempo real.
Revisar resultados
Al terminar se abre una ventana con todas las imágenes clasificadas en miniatura. Si alguna quedó en la categoría incorrecta, clic derecho → escribir la categoría correcta.

Estructura de salida
clasificadas/
├── seashore/
│   ├── playa_verano.jpg
│   └── atardecer.jpg
├── tabby_cat/
│   └── gato_durmiendo.png
├── birthday_cake/
│   └── cumpleaños.jpg
└── ...

Notas

Las imágenes originales no se eliminan — el script hace copias
Formatos soportados: .jpg, .jpeg, .png
La primera vez tarda un poco más mientras descarga los pesos del modelo (~100 MB)


Autor
Ana Maraboli
@AnaMaraboli
Creadora de contenido | Python | IA aplicada

Construido para resolver un problema real: miles de fotos de contenido dispersas sin orden.
