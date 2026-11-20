from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
import logging
import re
from typing import Any, Optional


# =====================================================================
# CONFIGURACIÓN DE LOGS (REGISTRO DE EVENTOS Y ERRORES EN ARCHIVO)
# =====================================================================
def configurar_logger(nombre_archivo: str = "eventos_software_fj.log") -> logging.Logger:
    """Configura y devuelve un logger que escribe eventos y errores en archivo."""
    logger = logging.getLogger("SoftwareFJLogger")
    logger.setLevel(logging.INFO)

    # Evita duplicar handlers si se reejecuta en el mismo entorno
    if not logger.handlers:
        formato = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        file_handler = logging.FileHandler(nombre_archivo, mode="w", encoding="utf-8")
        file_handler.setFormatter(formato)
        logger.addHandler(file_handler)

    return logger


logger = configurar_logger()


# =====================================================================
# EXCEPCIONES PERSONALIZADAS DEL DOMINIO
# =====================================================================
class ErrorSoftwareFJ(Exception):
    """Excepción base para errores controlados en el sistema de Software FJ."""


class ErrorValidacionDato(ErrorSoftwareFJ):
    """Se lanza cuando un dato ingresado no cumple las reglas de validación."""


class ErrorParametroFaltante(ErrorSoftwareFJ):
    """Se lanza cuando falta un parámetro obligatorio o es vacío."""


class ErrorOperacionNoPermitida(ErrorSoftwareFJ):
    """Se lanza ante transiciones de estado o acciones inválidas."""


class ErrorServicioNoDisponible(ErrorSoftwareFJ):
    """Se lanza cuando un servicio no está disponible o tiene parámetros inválidos."""


class ErrorCalculoCosto(ErrorSoftwareFJ):
    """Se lanza cuando ocurre un error o inconsistencia al calcular costos."""


# =====================================================================
# CLASE ABSTRACTA GENERAL DEL SISTEMA
# =====================================================================
class EntidadSistema(ABC):
    """Clase abstracta base para entidades generales de Software FJ."""

    def __init__(self, id_entidad: str) -> None:
        # Valida que el identificador no esté vacío
        if not isinstance(id_entidad, str) or not id_entidad.strip():
            raise ErrorParametroFaltante("El identificador de la entidad es obligatorio.")
        self._id_entidad = id_entidad.strip()

    @property
    def id_entidad(self) -> str:
        """Retorna el identificador único de la entidad."""
        return self._id_entidad

    @abstractmethod
    def resumen(self) -> str:
        """Retorna una descripción resumida de la entidad."""


# =====================================================================
# CLASE CLIENTE CON ENCAPSULACIÓN Y VALIDACIONES
# =====================================================================
class Cliente(EntidadSistema):
    """Representa un cliente con datos encapsulados y validaciones estrictas."""

    def __init__(self, id_cliente: str, nombre: str, correo: str, activo: bool = True) -> None:
        super().__init__(id_cliente)
        self.__nombre = ""
        self.__correo = ""
        self.__activo = bool(activo)

        # Usa los setters para aplicar validaciones desde la construcción
        self.nombre = nombre
        self.correo = correo

    @property
    def nombre(self) -> str:
        """Obtiene el nombre del cliente."""
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """Valida y asigna el nombre del cliente."""
        if not isinstance(valor, str) or not valor.strip():
            raise ErrorParametroFaltante("El nombre del cliente no puede estar vacío.")
        if len(valor.strip()) < 3:
            raise ErrorValidacionDato("El nombre del cliente debe tener al menos 3 caracteres.")
        self.__nombre = valor.strip()

    @property
    def correo(self) -> str:
        """Obtiene el correo electrónico encapsulado."""
        return self.__correo

    @correo.setter
    def correo(self, valor: str) -> None:
        """Valida el formato del correo electrónico antes de asignarlo."""
        if not isinstance(valor, str) or not valor.strip():
            raise ErrorParametroFaltante("El correo del cliente es obligatorio.")
        patron_correo = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
        if not re.match(patron_correo, valor.strip()):
            raise ErrorValidacionDato(f"Correo electrónico inválido: '{valor}'.")
        self.__correo = valor.strip().lower()

    @property
    def activo(self) -> bool:
        """Indica si el cliente se encuentra activo."""
        return self.__activo

    @activo.setter
    def activo(self, estado: bool) -> None:
        """Actualiza el estado activo/inactivo del cliente."""
        if not isinstance(estado, bool):
            raise ErrorValidacionDato("El estado 'activo' debe ser booleano (True/False).")
        self.__activo = estado

    def resumen(self) -> str:
        """Devuelve un resumen legible del cliente."""
        estado_txt = "Activo" if self.__activo else "Inactivo"
        return f"Cliente[{self._id_entidad}] - {self.__nombre} ({self.__correo}) [{estado_txt}]"


# =====================================================================
# CLASE ABSTRACTA SERVICIO Y SERVICIOS DERIVADOS (POLIMORFISMO)
# =====================================================================
class Servicio(EntidadSistema, ABC):
    """Clase abstracta para los servicios ofrecidos por Software FJ."""

    def __init__(
        self,
        id_servicio: str,
        nombre_servicio: str,
        tarifa_base: float,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio)
        if not isinstance(nombre_servicio, str) or not nombre_servicio.strip():
            raise ErrorParametroFaltante("El nombre del servicio es obligatorio.")
        if not isinstance(tarifa_base, (int, float)) or tarifa_base <= 0:
            raise ErrorValidacionDato("La tarifa base del servicio debe ser un número mayor a 0.")
        if not isinstance(disponible, bool):
            raise ErrorValidacionDato("El campo 'disponible' debe ser booleano.")

        self._nombre_servicio = nombre_servicio.strip()
        self._tarifa_base = float(tarifa_base)
        self._disponible = disponible

    @property
    def nombre_servicio(self) -> str:
        return self._nombre_servicio

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        if not isinstance(estado, bool):
            raise ErrorValidacionDato("La disponibilidad debe ser un valor booleano.")
        self._disponible = estado

    @abstractmethod
    def validar_parametros(self, duracion_horas: int, **kwargs: Any) -> None:
        """Valida la duración y parámetros específicos de cada tipo de servicio."""

    @abstractmethod
    def describir(self) -> str:
        """Describe las características particulares del servicio."""

    @abstractmethod
    def _calcular_subtotal_base(self, duracion_horas: int, **kwargs: Any) -> float:
        """Calcula el subtotal antes de descuentos o impuestos según el tipo de servicio."""

    def calcular_costo(
        self,
        duracion_horas: int,
        descuento_porc: float = 0.0,
        impuesto_porc: float = 0.0,
        **kwargs: Any,
    ) -> float:
        """
        Método con parámetros opcionales (variantes de cálculo de costos):
        - Sin opcionales: calcular_costo(duracion)
        - Con descuento: calcular_costo(duracion, descuento_porc=10)
        - Con descuento e impuesto: calcular_costo(duracion, descuento_porc=10, impuesto_porc=19)
        """
        try:
            # Verifica disponibilidad antes de cotizar/calcular
            if not self._disponible:
                raise ErrorServicioNoDisponible(
                    f"El servicio '{self._nombre_servicio}' no está disponible actualmente."
                )

            # Valida parámetros del servicio concreto
            self.validar_parametros(duracion_horas, **kwargs)

            # Valida porcentajes de descuento e impuesto
            if not isinstance(descuento_porc, (int, float)) or not (0 <= descuento_porc < 100):
                raise ErrorCalculoCosto("El porcentaje de descuento debe estar entre 0 y 99.9.")
            if not isinstance(impuesto_porc, (int, float)) or impuesto_porc < 0:
                raise ErrorCalculoCosto("El porcentaje de impuesto no puede ser negativo.")

            subtotal = self._calcular_subtotal_base(duracion_horas, **kwargs)
            con_descuento = subtotal * (1 - float(descuento_porc) / 100.0)
            total = con_descuento * (1 + float(impuesto_porc) / 100.0)

            if total <= 0:
                raise ErrorCalculoCosto("El costo total calculado es inconsistente (menor o igual a 0).")

            return round(float(total), 2)

        except ErrorSoftwareFJ:
            # Propaga excepciones propias ya contextualizadas
            raise
        except Exception as exc:
            # Encadena excepciones inesperadas de bajo nivel (ej. TypeError/ZeroDivisionError)
            raise ErrorCalculoCosto(
                f"Error inesperado al calcular costo del servicio '{self._nombre_servicio}'."
            ) from exc

    def resumen(self) -> str:
        estado = "Disponible" if self._disponible else "No disponible"
        return f"{self.describir()} | Tarifa base: ${self._tarifa_base:.2f} | {estado}"


class ReservaSala(Servicio):
    """Servicio especializado para reserva de salas de reuniones o capacitación."""

    def __init__(
        self,
        id_servicio: str,
        nombre_servicio: str,
        tarifa_base: float,
        capacidad_maxima: int,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre_servicio, tarifa_base, disponible)
        if not isinstance(capacidad_maxima, int) or capacidad_maxima <= 0:
            raise ErrorValidacionDato("La capacidad máxima de la sala debe ser un entero positivo.")
        self.capacidad_maxima = capacidad_maxima

    def validar_parametros(self, duracion_horas: int, **kwargs: Any) -> None:
        if not isinstance(duracion_horas, int) or duracion_horas <= 0:
            raise ErrorValidacionDato("La duración de la reserva de sala debe ser al menos 1 hora.")
        asistentes = kwargs.get("asistentes", 1)
        if not isinstance(asistentes, int) or asistentes <= 0:
            raise ErrorValidacionDato("El número de asistentes debe ser un entero positivo.")
        if asistentes > self.capacidad_maxima:
            raise ErrorServicioNoDisponible(
                f"Los asistentes ({asistentes}) superan la capacidad de la sala ({self.capacidad_maxima})."
            )

    def _calcular_subtotal_base(self, duracion_horas: int, **kwargs: Any) -> float:
        return self._tarifa_base * duracion_horas

    def describir(self) -> str:
        return (
            f"Sala[{self._id_entidad}] '{self._nombre_servicio}' "
            f"(Capacidad máx.: {self.capacidad_maxima} personas)"
        )


class AlquilerEquipo(Servicio):
    """Servicio especializado para alquiler de equipos tecnológicos."""

    def __init__(
        self,
        id_servicio: str,
        nombre_servicio: str,
        tarifa_base: float,
        unidades_disponibles: int,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre_servicio, tarifa_base, disponible)
        if not isinstance(unidades_disponibles, int) or unidades_disponibles < 0:
            raise ErrorValidacionDato("Las unidades disponibles deben ser un entero mayor o igual a 0.")
        self.unidades_disponibles = unidades_disponibles

    def validar_parametros(self, duracion_horas: int, **kwargs: Any) -> None:
        if not isinstance(duracion_horas, int) or duracion_horas <= 0:
            raise ErrorValidacionDato("La duración del alquiler debe ser un entero positivo.")
        unidades = kwargs.get("unidades", 1)
        if not isinstance(unidades, int) or unidades <= 0:
            raise ErrorValidacionDato("La cantidad de unidades a alquilar debe ser mayor a 0.")
        if unidades > self.unidades_disponibles:
            raise ErrorServicioNoDisponible(
                f"Solicitadas {unidades} unidades, pero solo hay {self.unidades_disponibles} disponibles."
            )

    def _calcular_subtotal_base(self, duracion_horas: int, **kwargs: Any) -> float:
        unidades = kwargs.get("unidades", 1)
        return self._tarifa_base * duracion_horas * unidades

    def describir(self) -> str:
        return (
            f"Equipo[{self._id_entidad}] '{self._nombre_servicio}' "
            f"(Stock: {self.unidades_disponibles} und.)"
        )


class AsesoriaEspecializada(Servicio):
    """Servicio especializado para consultoría o asesoría técnica."""

    def __init__(
        self,
        id_servicio: str,
        nombre_servicio: str,
        tarifa_base: float,
        especialidad: str,
        disponible: bool = True,
    ) -> None:
        super().__init__(id_servicio, nombre_servicio, tarifa_base, disponible)
        if not isinstance(especialidad, str) or not especialidad.strip():
            raise ErrorParametroFaltante("La especialidad de la asesoría es obligatoria.")
        self.especialidad = especialidad.strip()

    def validar_parametros(self, duracion_horas: int, **kwargs: Any) -> None:
        if not isinstance(duracion_horas, int) or not (1 <= duracion_horas <= 12):
            raise ErrorValidacionDato(
                "La asesoría especializada debe tener una duración entre 1 y 12 horas."
            )

    def _calcular_subtotal_base(self, duracion_horas: int, **kwargs: Any) -> float:
        # Recargo leve si la asesoría supera 4 horas continuas
        recargo_extension = 1.15 if duracion_horas > 4 else 1.0
        return self._tarifa_base * duracion_horas * recargo_extension

    def describir(self) -> str:
        return (
            f"Asesoría[{self._id_entidad}] '{self._nombre_servicio}' "
            f"(Área: {self.especialidad})"
        )


# =====================================================================
# CLASE RESERVA CON ESTADOS Y PROCESAMIENTO CON EXCEPCIONES
# =====================================================================
class Reserva(EntidadSistema):
    """Integra cliente, servicio, duración y estado, con confirmación y cancelación."""

    ESTADOS_VALIDOS = ("PENDIENTE", "CONFIRMADA", "CANCELADA")

    def __init__(
        self,
        id_reserva: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion_horas: int,
        descuento_porc: float = 0.0,
        impuesto_porc: float = 0.0,
        **parametros_servicio: Any,
    ) -> None:
        super().__init__(id_reserva)

        if not isinstance(cliente, Cliente):
            raise ErrorValidacionDato("Debe asociarse una instancia válida de Cliente.")
        if not cliente.activo:
            raise ErrorOperacionNoPermitida(
                f"El cliente '{cliente.nombre}' está inactivo y no puede realizar reservas."
            )
        if not isinstance(servicio, Servicio):
            raise ErrorValidacionDato("Debe asociarse una instancia válida de Servicio.")

        self.cliente = cliente
        self.servicio = servicio
        self.duracion_horas = duracion_horas
        self.descuento_porc = descuento_porc
        self.impuesto_porc = impuesto_porc
        self.parametros_servicio = parametros_servicio
        self.estado = "PENDIENTE"
        self.costo_total = self.servicio.calcular_costo(
            duracion_horas=self.duracion_horas,
            descuento_porc=self.descuento_porc,
            impuesto_porc=self.impuesto_porc,
            **self.parametros_servicio,
        )

    def confirmar(self) -> None:
        """Confirma una reserva pendiente."""
        if self.estado == "CANCELADA":
            raise ErrorOperacionNoPermitida(
                f"No se puede confirmar la reserva '{self._id_entidad}' porque está cancelada."
            )
        if self.estado == "CONFIRMADA":
            raise ErrorOperacionNoPermitida(
                f"La reserva '{self._id_entidad}' ya se encuentra confirmada."
            )
        self.estado = "CONFIRMADA"

    def cancelar(self) -> None:
        """Cancela una reserva si no ha sido cancelada previamente."""
        if self.estado == "CANCELADA":
            raise ErrorOperacionNoPermitida(
                f"La reserva '{self._id_entidad}' ya está cancelada."
            )
        self.estado = "CANCELADA"

    def procesar(self, accion: str = "confirmar") -> str:
        """
        Procesa la reserva aplicando try/except/else/finally y registrando en log.
        """
        accion_limpia = accion.strip().lower()
        procesado_ok = False

        try:
            if accion_limpia == "confirmar":
                self.confirmar()
            elif accion_limpia == "cancelar":
                self.cancelar()
            else:
                raise ErrorOperacionNoPermitida(f"Acción de reserva no reconocida: '{accion}'.")

        except ErrorSoftwareFJ as err:
            logger.error("Fallo al procesar reserva %s (%s): %s", self._id_entidad, accion_limpia, err)
            raise
        except Exception as err:
            # Encadena cualquier error imprevisto
            error_encadenado = ErrorOperacionNoPermitida(
                f"Error inesperado procesando la reserva '{self._id_entidad}'."
            )
            logger.exception("Error inesperado en reserva %s", self._id_entidad)
            raise error_encadenado from err
        else:
            # Se ejecuta solo si no hubo excepción en try
            procesado_ok = True
            logger.info(
                "Reserva %s procesada (%s) | Cliente: %s | Servicio: %s | Total: $%.2f | Estado: %s",
                self._id_entidad,
                accion_limpia,
                self.cliente.nombre,
                self.servicio.nombre_servicio,
                self.costo_total,
                self.estado,
            )
        finally:
            # Siempre se ejecuta al salir del bloque
            logger.info(
                "Fin del intento de procesamiento de reserva %s | Éxito=%s | Estado actual=%s",
                self._id_entidad,
                procesado_ok,
                self.estado,
            )

        return f"Reserva {self._id_entidad} en estado {self.estado} (Total: ${self.costo_total:.2f})"

    def resumen(self) -> str:
        return (
            f"Reserva[{self._id_entidad}] | Cliente: {self.cliente.nombre} | "
            f"Servicio: {self.servicio.nombre_servicio} | {self.duracion_horas}h | "
            f"Total: ${self.costo_total:.2f} | Estado: {self.estado}"
        )


# =====================================================================
# GESTOR EN MEMORIA (LISTAS DE OBJETOS, SIN BASE DE DATOS)
# =====================================================================
class GestorSoftwareFJ:
    """Administra clientes, servicios y reservas en listas en memoria."""

    def __init__(self) -> None:
        self.clientes: list[Cliente] = []
        self.servicios: list[Servicio] = []
        self.reservas: list[Reserva] = []

    def registrar_cliente(self, cliente: Cliente) -> None:
        """Agrega un cliente a la lista verificando que no exista duplicado."""
        if any(c.id_entidad == cliente.id_entidad for c in self.clientes):
            raise ErrorOperacionNoPermitida(f"Ya existe un cliente con ID '{cliente.id_entidad}'.")
        self.clientes.append(cliente)
        logger.info("Cliente registrado: %s", cliente.resumen())

    def registrar_servicio(self, servicio: Servicio) -> None:
        """Agrega un servicio a la lista verificando que no exista duplicado."""
        if any(s.id_entidad == servicio.id_entidad for s in self.servicios):
            raise ErrorOperacionNoPermitida(f"Ya existe un servicio con ID '{servicio.id_entidad}'.")
        self.servicios.append(servicio)
        logger.info("Servicio registrado: %s", servicio.resumen())

    def crear_reserva(self, reserva: Reserva) -> None:
        """Registra una reserva válida en la lista en memoria."""
        if any(r.id_entidad == reserva.id_entidad for r in self.reservas):
            raise ErrorOperacionNoPermitida(f"Ya existe una reserva con ID '{reserva.id_entidad}'.")
        self.reservas.append(reserva)
        logger.info("Reserva creada: %s", reserva.resumen())


# =====================================================================
# SIMULACIÓN DE 10 OPERACIONES COMPLETAS (VÁLIDAS E INVÁLIDAS)
# =====================================================================
def ejecutar_simulacion() -> None:
    """Ejecuta 10 operaciones de prueba manteniendo el sistema activo ante errores."""
    gestor = GestorSoftwareFJ()
    print("=== INICIO DE SIMULACIÓN SOFTWARE FJ (SIN BASE DE DATOS) ===\n")

    # Operación 1: Registro válido de cliente
    try:
        c1 = Cliente("CLI-01", "Laura Gómez", "laura.gomez@empresa.com", activo=True)
        gestor.registrar_cliente(c1)
        print("[OP 1 - ÉXITO] Cliente registrado:", c1.resumen())
    except ErrorSoftwareFJ as e:
        logger.error("OP 1 falló: %s", e)
        print("[OP 1 - ERROR CONTROLADO]", e)

    # Operación 2: Registro inválido de cliente (correo mal formado)
    try:
        c_invalido = Cliente("CLI-02", "Carlos Ruiz", "carlos_sin_arroba.com")
        gestor.registrar_cliente(c_invalido)
        print("[OP 2 - ÉXITO]")
    except ErrorSoftwareFJ as e:
        logger.error("OP 2 falló: %s", e)
        print("[OP 2 - ERROR CONTROLADO]", e)

    # Operación 3: Registro válido de segundo cliente (inactivo para probar restricción)
    try:
        c3 = Cliente("CLI-03", "Andrés Pérez", "andres.perez@correo.co", activo=False)
        gestor.registrar_cliente(c3)
        print("[OP 3 - ÉXITO] Cliente registrado:", c3.resumen())
    except ErrorSoftwareFJ as e:
        logger.error("OP 3 falló: %s", e)
        print("[OP 3 - ERROR CONTROLADO]", e)

    # Operación 4: Creación correcta de servicios especializados (Sala, Equipo, Asesoría)
    try:
        s_sala = ReservaSala("SRV-01", "Sala de Juntas Norte", 80.0, capacidad_maxima=12)
        s_equipo = AlquilerEquipo("SRV-02", "Laptop Workstation", 25.0, unidades_disponibles=5)
        s_asesoria = AsesoriaEspecializada("SRV-03", "Arquitectura Cloud", 120.0, "AWS y Microservicios")
        for srv in (s_sala, s_equipo, s_asesoria):
            gestor.registrar_servicio(srv)
        print("[OP 4 - ÉXITO] 3 servicios registrados correctamente.")
    except ErrorSoftwareFJ as e:
        logger.error("OP 4 falló: %s", e)
        print("[OP 4 - ERROR CONTROLADO]", e)

    # Operación 5: Creación incorrecta de servicio (tarifa negativa / parámetro faltante)
    try:
        s_malo = AsesoriaEspecializada("SRV-04", "Consultoría QA", -50.0, "")
        gestor.registrar_servicio(s_malo)
        print("[OP 5 - ÉXITO]")
    except ErrorSoftwareFJ as e:
        logger.error("OP 5 falló: %s", e)
        print("[OP 5 - ERROR CONTROLADO]", e)

    # Operación 6: Reserva exitosa de sala (con descuento e impuesto)
    r1: Optional[Reserva] = None
    try:
        r1 = Reserva(
            "RES-01",
            gestor.clientes[0],
            gestor.servicios[0],
            duracion_horas=3,
            descuento_porc=10.0,
            impuesto_porc=19.0,
            asistentes=8,
        )
        gestor.crear_reserva(r1)
        mensaje = r1.procesar("confirmar")
        print("[OP 6 - ÉXITO]", mensaje)
    except ErrorSoftwareFJ as e:
        logger.error("OP 6 falló: %s", e)
        print("[OP 6 - ERROR CONTROLADO]", e)

    # Operación 7: Reserva fallida por cliente inactivo
    try:
        r_inactiva = Reserva(
            "RES-02",
            gestor.clientes[1],  # Andrés Pérez (activo=False)
            gestor.servicios[1],
            duracion_horas=2,
            unidades=1,
        )
        gestor.crear_reserva(r_inactiva)
        print("[OP 7 - ÉXITO]")
    except ErrorSoftwareFJ as e:
        logger.error("OP 7 falló: %s", e)
        print("[OP 7 - ERROR CONTROLADO]", e)

    # Operación 8: Reserva fallida por exceder capacidad o unidades disponibles
    try:
        r_exceso = Reserva(
            "RES-03",
            gestor.clientes[0],
            gestor.servicios[1],  # Laptop Workstation (stock=5)
            duracion_horas=4,
            unidades=9,
        )
        gestor.crear_reserva(r_exceso)
        print("[OP 8 - ÉXITO]")
    except ErrorSoftwareFJ as e:
        logger.error("OP 8 falló: %s", e)
        print("[OP 8 - ERROR CONTROLADO]", e)

    # Operación 9: Reserva exitosa de asesoría y posterior cancelación
    try:
        r2 = Reserva(
            "RES-04",
            gestor.clientes[0],
            gestor.servicios[2],
            duracion_horas=5,
        )
        gestor.crear_reserva(r2)
        r2.procesar("confirmar")
        estado_cancel = r2.procesar("cancelar")
        print("[OP 9 - ÉXITO]", estado_cancel)
    except ErrorSoftwareFJ as e:
        logger.error("OP 9 falló: %s", e)
        print("[OP 9 - ERROR CONTROLADO]", e)

    # Operación 10: Operación inválida sobre reserva ya cancelada (confirmar tras cancelar)
    try:
        if r2 is None:
            raise ErrorOperacionNoPermitida("No existe la reserva RES-04 para probar la transición.")
        r2.procesar("confirmar")
        print("[OP 10 - ÉXITO]")
    except ErrorSoftwareFJ as e:
        logger.error("OP 10 falló: %s", e)
        print("[OP 10 - ERROR CONTROLADO]", e)

    print("\n=== ESTADO FINAL EN MEMORIA ===")
    print(f"Clientes registrados: {len(gestor.clientes)}")
    print(f"Servicios registrados: {len(gestor.servicios)}")
    print(f"Reservas registradas: {len(gestor.reservas)}")
    print("Revisa el archivo 'eventos_software_fj.log' para ver el historial detallado.")


if __name__ == "__main__":
    ejecutar_simulacion()