from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Mantenimiento

# Tests para el módulo maintenance: registro de mantenimientos, tipos de mantenimiento,
# estados de mantenimiento y filtrado de registros de mantenimiento
class MantenimientoTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_message_shown = False

    def get_status_description(self, status_code):
        """Retorna una descripción amigable del código de estado HTTP"""
        status_descriptions = {
            200: "OK - La solicitud se completó exitosamente",
            400: "Bad Request - La solicitud contiene errores",
            404: "Not Found - Recurso no encontrado",
        }
        return status_descriptions.get(status_code, f"Código {status_code} - No documentado")

    def setUp(self):
        if not self.__class__._setup_message_shown:
            print("\n" + "="*65)
            print("="*65)
            print("="*12 + "  TEST DE MAINTENANCE  " + "="*31)
            print("="*65)
            print("="*65)
            self.client = Client()
            print("✓ Cliente de prueba inicializado")
            print("-"*50)
            self.__class__._setup_message_shown = True
        else:
            self.client = Client()

    def test_crear_mantenimiento_correctivo(self):
        print("\n" + "="*50)
        print("TEST: CREAR MANTENIMIENTO CORRECTIVO")
        print("="*50)
        print("• Creando mantenimiento correctivo...")
        mantenimiento = Mantenimiento.objects.create(
            tipo='CORRECTIVO',
            descripcion='Se detectó un error en el módulo de inventario',
            modulo_afectado='Inventario',
            acciones_realizadas='Se realizó corrección del bug en la actualización de stock'
        )
        print("\n✓ Mantenimiento creado:")
        print(f"  → ID: {mantenimiento.id}")
        print(f"  → Tipo: {mantenimiento.get_tipo_display()}")
        print(f"  → Descripción: {mantenimiento.descripcion}")
        print(f"  → Módulo afectado: {mantenimiento.modulo_afectado}")
        print(f"  → Estado: {mantenimiento.get_estado_display()}")
        print(f"  → Acciones realizadas: {mantenimiento.acciones_realizadas}")
        
        self.assertEqual(mantenimiento.tipo, 'CORRECTIVO')
        self.assertEqual(mantenimiento.modulo_afectado, 'Inventario')
        self.assertEqual(mantenimiento.estado, 'PENDIENTE')
        print("-"*50)

    def test_crear_mantenimiento_preventivo(self):
        print("\n" + "="*50)
        print("TEST: CREAR MANTENIMIENTO PREVENTIVO")
        print("="*50)
        print("• Creando mantenimiento preventivo...")
        mantenimiento = Mantenimiento.objects.create(
            tipo='PREVENTIVO',
            descripcion='Revisión periódica del sistema',
            modulo_afectado='Sistema',
            acciones_realizadas='Se realizó actualización de dependencias'
        )
        print("\n✓ Mantenimiento preventivo creado:")
        print(f"  → Tipo: {mantenimiento.get_tipo_display()}")
        print(f"  → Módulo: {mantenimiento.modulo_afectado}")
        
        self.assertEqual(mantenimiento.tipo, 'PREVENTIVO')
        print("-"*50)

    def test_crear_mantenimiento_adaptativo(self):
        print("\n" + "="*50)
        print("TEST: CREAR MANTENIMIENTO ADAPTATIVO")
        print("="*50)
        print("• Creando mantenimiento adaptativo...")
        mantenimiento = Mantenimiento.objects.create(
            tipo='ADAPTATIVO',
            descripcion='Adaptación del sistema a nuevos requerimientos',
            modulo_afectado='Ventas',
            acciones_realizadas='Se agregó nueva funcionalidad de descuentos'
        )
        print("\n✓ Mantenimiento adaptativo creado:")
        print(f"  → Tipo: {mantenimiento.get_tipo_display()}")
        
        self.assertEqual(mantenimiento.tipo, 'ADAPTATIVO')
        print("-"*50)

    def test_crear_mantenimiento_perfectivo(self):
        print("\n" + "="*50)
        print("TEST: CREAR MANTENIMIENTO PERFECTIVO")
        print("="*50)
        print("• Creando mantenimiento perfectivo...")
        mantenimiento = Mantenimiento.objects.create(
            tipo='PERFECTIVO',
            descripcion='Mejora de rendimiento del sistema',
            modulo_afectado='Base de Datos',
            acciones_realizadas='Se optimizaron las consultas SQL'
        )
        print("\n✓ Mantenimiento perfectivo creado:")
        print(f"  → Tipo: {mantenimiento.get_tipo_display()}")
        
        self.assertEqual(mantenimiento.tipo, 'PERFECTIVO')
        print("-"*50)

    def test_cambiar_estado_a_en_proceso(self):
        print("\n" + "="*50)
        print("TEST: CAMBIAR ESTADO A EN PROCESO")
        print("="*50)
        print("• Creando mantenimiento...")
        mantenimiento = Mantenimiento.objects.create(
            tipo='CORRECTIVO',
            descripcion='Error crítico',
            modulo_afectado='Inventario',
            acciones_realizadas='Análisis en progreso'
        )
        print(f"  → Estado inicial: {mantenimiento.get_estado_display()}")
        
        print("\n• Cambiando estado a EN_PROCESO...")
        mantenimiento.estado = 'EN_PROCESO'
        mantenimiento.save()
        
        print(f"  → Estado actual: {mantenimiento.get_estado_display()}")
        self.assertEqual(mantenimiento.estado, 'EN_PROCESO')
        print("-"*50)

    def test_cambiar_estado_a_completado(self):
        print("\n" + "="*50)
        print("TEST: CAMBIAR ESTADO A COMPLETADO")
        print("="*50)
        print("• Creando mantenimiento...")
        mantenimiento = Mantenimiento.objects.create(
            tipo='CORRECTIVO',
            descripcion='Error corregido',
            modulo_afectado='Ventas',
            acciones_realizadas='Problema resuelto'
        )
        print(f"  → Estado inicial: {mantenimiento.get_estado_display()}")
        
        print("\n• Cambiando estado a EN_PROCESO -> COMPLETADO...")
        mantenimiento.estado = 'EN_PROCESO'
        mantenimiento.save()
        mantenimiento.estado = 'COMPLETADO'
        mantenimiento.save()
        
        print(f"  → Estado final: {mantenimiento.get_estado_display()}")
        self.assertEqual(mantenimiento.estado, 'COMPLETADO')
        print("-"*50)

    def test_timestamp_automatico(self):
        print("\n" + "="*50)
        print("TEST: TIMESTAMP AUTOMÁTICO")
        print("="*50)
        print("• Creando mantenimiento...")
        ahora_antes = timezone.now()
        mantenimiento = Mantenimiento.objects.create(
            tipo='PREVENTIVO',
            descripcion='Revisión',
            modulo_afectado='Sistema',
            acciones_realizadas='Revisión completada'
        )
        ahora_despues = timezone.now()
        
        print("\n✓ Timestamp verificado:")
        print(f"  → Hora antes: {ahora_antes}")
        print(f"  → Fecha registrada: {mantenimiento.fecha}")
        print(f"  → Hora después: {ahora_despues}")
        print(f"  → ¿Timestamp válido?: {ahora_antes <= mantenimiento.fecha <= ahora_despues}")
        
        self.assertGreaterEqual(mantenimiento.fecha, ahora_antes)
        self.assertLessEqual(mantenimiento.fecha, ahora_despues)
        print("-"*50)

    def test_filtrar_por_tipo(self):
        print("\n" + "="*50)
        print("TEST: FILTRAR MANTENIMIENTOS POR TIPO")
        print("="*50)
        print("• Creando mantenimientos de diferentes tipos...")
        Mantenimiento.objects.create(tipo='CORRECTIVO', descripcion='Error 1', 
                                     modulo_afectado='Inventario', acciones_realizadas='Acción 1')
        Mantenimiento.objects.create(tipo='CORRECTIVO', descripcion='Error 2', 
                                     modulo_afectado='Ventas', acciones_realizadas='Acción 2')
        Mantenimiento.objects.create(tipo='PREVENTIVO', descripcion='Revisión', 
                                     modulo_afectado='Sistema', acciones_realizadas='Acción 3')
        
        print("\n• Filtrando por tipo 'CORRECTIVO'...")
        correctivos = Mantenimiento.objects.filter(tipo='CORRECTIVO')
        print(f"  → Mantenimientos correctivos: {correctivos.count()}")
        
        self.assertEqual(correctivos.count(), 2)
        print("-"*50)

    def test_filtrar_por_modulo(self):
        print("\n" + "="*50)
        print("TEST: FILTRAR MANTENIMIENTOS POR MÓDULO")
        print("="*50)
        print("• Creando mantenimientos de diferentes módulos...")
        Mantenimiento.objects.create(tipo='CORRECTIVO', descripcion='Error Inventario 1', 
                                     modulo_afectado='Inventario', acciones_realizadas='Acción 1')
        Mantenimiento.objects.create(tipo='CORRECTIVO', descripcion='Error Inventario 2', 
                                     modulo_afectado='Inventario', acciones_realizadas='Acción 2')
        Mantenimiento.objects.create(tipo='PREVENTIVO', descripcion='Revisión Ventas', 
                                     modulo_afectado='Ventas', acciones_realizadas='Acción 3')
        
        print("\n• Filtrando por módulo 'Inventario'...")
        inventario_mant = Mantenimiento.objects.filter(modulo_afectado='Inventario')
        print(f"  → Mantenimientos de Inventario: {inventario_mant.count()}")
        
        self.assertEqual(inventario_mant.count(), 2)
        print("-"*50)

    def test_filtrar_por_estado(self):
        print("\n" + "="*50)
        print("TEST: FILTRAR MANTENIMIENTOS POR ESTADO")
        print("="*50)
        print("• Creando mantenimientos con diferentes estados...")
        m1 = Mantenimiento.objects.create(tipo='CORRECTIVO', descripcion='Pendiente', 
                                          modulo_afectado='Inventario', acciones_realizadas='Acción 1')
        m2 = Mantenimiento.objects.create(tipo='PREVENTIVO', descripcion='En proceso', 
                                          modulo_afectado='Ventas', acciones_realizadas='Acción 2')
        m2.estado = 'EN_PROCESO'
        m2.save()
        
        m3 = Mantenimiento.objects.create(tipo='ADAPTATIVO', descripcion='Completado', 
                                          modulo_afectado='Sistema', acciones_realizadas='Acción 3')
        m3.estado = 'COMPLETADO'
        m3.save()
        
        print("\n• Filtrando por estado 'PENDIENTE'...")
        pendientes = Mantenimiento.objects.filter(estado='PENDIENTE')
        print(f"  → Mantenimientos pendientes: {pendientes.count()}")
        
        print("\n• Filtrando por estado 'EN_PROCESO'...")
        en_proceso = Mantenimiento.objects.filter(estado='EN_PROCESO')
        print(f"  → Mantenimientos en proceso: {en_proceso.count()}")
        
        print("\n• Filtrando por estado 'COMPLETADO'...")
        completados = Mantenimiento.objects.filter(estado='COMPLETADO')
        print(f"  → Mantenimientos completados: {completados.count()}")
        
        self.assertEqual(pendientes.count(), 1)
        self.assertEqual(en_proceso.count(), 1)
        self.assertEqual(completados.count(), 1)
        print("-"*50)

    def test_ordenamiento_por_fecha(self):
        print("\n" + "="*50)
        print("TEST: ORDENAMIENTO POR FECHA (MÁS RECIENTE PRIMERO)")
        print("="*50)
        print("• Creando mantenimientos con diferentes fechas...")
        
        m1 = Mantenimiento.objects.create(tipo='CORRECTIVO', descripcion='Primero', 
                                          modulo_afectado='Inventario', acciones_realizadas='Acción 1')
        m1.fecha = timezone.now() - timedelta(hours=3)
        m1.save()
        
        m2 = Mantenimiento.objects.create(tipo='PREVENTIVO', descripcion='Segundo', 
                                          modulo_afectado='Ventas', acciones_realizadas='Acción 2')
        m2.fecha = timezone.now() - timedelta(hours=2)
        m2.save()
        
        m3 = Mantenimiento.objects.create(tipo='ADAPTATIVO', descripcion='Tercero', 
                                          modulo_afectado='Sistema', acciones_realizadas='Acción 3')
        m3.fecha = timezone.now() - timedelta(hours=1)
        m3.save()
        
        print("\n• Obteniendo mantenimientos ordenados...")
        mantenimientos = Mantenimiento.objects.all().order_by('-fecha')
        print(f"  → Primero en lista: {mantenimientos[0].descripcion}")
        print(f"  → Último en lista: {mantenimientos[mantenimientos.count()-1].descripcion}")
        
        self.assertEqual(mantenimientos[0].descripcion, "Tercero")
        self.assertEqual(mantenimientos[mantenimientos.count()-1].descripcion, "Primero")
        print("-"*50)

    def test_str_representation(self):
        print("\n" + "="*50)
        print("TEST: REPRESENTACIÓN EN STRING (__STR__)")
        print("="*50)
        print("• Creando mantenimiento...")
        mantenimiento = Mantenimiento.objects.create(
            tipo='CORRECTIVO',
            descripcion='Test string',
            modulo_afectado='Inventario',
            acciones_realizadas='Acción'
        )
        
        str_rep = str(mantenimiento)
        print("\n✓ Representación en string:")
        print(f"  → {str_rep}")
        print(f"  → Contiene 'Correctivo': {'Correctivo' in str_rep}")
        print(f"  → Contiene 'Inventario': {'Inventario' in str_rep}")
        
        self.assertIn('Correctivo', str_rep)
        self.assertIn('Inventario', str_rep)
        print("-"*50)

    def test_combinacion_filtros(self):
        print("\n" + "="*50)
        print("TEST: COMBINACIÓN DE FILTROS")
        print("="*50)
        print("• Creando mantenimientos variados...")
        
        m1 = Mantenimiento.objects.create(tipo='CORRECTIVO', descripcion='Error Inventario', 
                                          modulo_afectado='Inventario', acciones_realizadas='Acción 1')
        m1.estado = 'COMPLETADO'
        m1.save()
        
        m2 = Mantenimiento.objects.create(tipo='CORRECTIVO', descripcion='Error Ventas', 
                                          modulo_afectado='Ventas', acciones_realizadas='Acción 2')
        
        m3 = Mantenimiento.objects.create(tipo='PREVENTIVO', descripcion='Revisión Inventario', 
                                          modulo_afectado='Inventario', acciones_realizadas='Acción 3')
        m3.estado = 'EN_PROCESO'
        m3.save()
        
        print("\n• Filtrando mantenimientos correctivos completados de Inventario...")
        resultado = Mantenimiento.objects.filter(
            tipo='CORRECTIVO',
            estado='COMPLETADO',
            modulo_afectado='Inventario'
        )
        print(f"  → Resultados: {resultado.count()}")
        
        self.assertEqual(resultado.count(), 1)
        print("-"*50)

    def tearDown(self):
        # Limpieza después de cada prueba
        Mantenimiento.objects.all().delete()
