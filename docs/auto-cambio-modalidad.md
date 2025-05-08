# Introducción

Cuando se hace un alta, o cuando un socio pide un cambio de modalidad, puede ser necesario gestionarlo en una fecha concreta... por ejemplo ha pagado el bimestre pero quiere seguir acudiendo a clases, o cambia de estar sin actividades a estar con actividades el curso siguiente.

# Operativa

Para hacer posible esta funcionalidad se ha definido una categoría llamada CAMBIOS con varias subcategorías llamadas:

- Cambio a socio CON actividades
- Cambio a socio SIN actividades
- Cambio a socio ADULTO CON actividades
- Cambio a socio ADULTO SIN actividades

así como un campo personalizado llamado `Fecha Cambio`

El script, comprueba si ha llegado la fecha guardada en 'Fecha Cambio', y de ser así, revisa las categorías destino y da de baja al usuario en las originales y lo da de alta en las nuevas.

Como las categorias 'con actividades' llevan asociado un cargo bimestral, establece también la fecha del próximo recibo para que se genere acorde al cambio de modalidad.
