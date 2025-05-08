# Introducción

Los futuros socios se registran en playoff para acudir a una charla de bienvenida, información sobre la asociación, etc.

Una vez han asistido, se les manda un enlace para aportar la documentación y que el equipo de psicólogos la revise.

Llegado a ese punto, el futuro socio figura como 'preinscrito' y al pasar las comprobaciones necesarias se 'Valida el alta' en playoff.

# Funcionamiento

El script de auto-alta (`4-auto-alta.py`) comprueba que, tal y como se le ha comunicado al 'Validar el alta' ha realizado la inscripción y pago via TPV de una actividad de alta, en cuyo caso, procede a seguir las preferencias del formulario de preinscripción (socio con actividades, sin actividades, adulto, etc.) y añadir las categorías necesarias.

Se acordó que todo socio de alta pueda acceder a las salidas familiares, eventos, por lo que a cada socio se le añade SIEMPRE al grupo de sin actividades (para evitar problemas con las remeasas) y se les programa, en caso de haber pedido alta con actividades, un cambio de categoría programado, para que de ese modo, cuando llegue la fecha, otro script `4-auto-cambios-modalidad.py` realice este cambio de modalidad del socio (más información del funcionamiento en la página sobre el auto cambio de modalidad).

Actualmente las altas se consideran en Septiembre y en Enero, para que se pueda coordinar con los equipos de acogida que realizan una visita a las instalaciones, una acogida con entrega de carnets, etc.
