from .views import *
from rest_framework.routers import DefaultRouter
from django.urls import path


router = DefaultRouter()
router.register(r'usuario', UsuarioCustomizadoView)
router.register(r'Guarda', GuardaView)
router.register(r'UsuarioGuarda', UsuarioGuardaView)
router.register(r'Troca', TrocaView)
router.register(r'TrocaAtirador', TrocaAtiradorView)
router.register(r'TrocaGuarda', TrocaGuardaView)
router.register(r'Notificacao', NotificacaoView)
router.register(r'Escala', EscalaView)

custom_urls = [
    path('solicitar-troca/', solicitar_troca_guarda, name='solicitar-troca'),
    path('sortear_guardas/', sortear_guardas, name='sortear_guardas'),
    path('apagar_guardas/', apagar_guardas, name='apagar_guardas'),
    path('guardas-agrupadas/', guardas_agrupadas, name='guardas_agrupadas'),
    path('aceitar-troca/', aceitar_troca, name='aceitar_troca'),
    path('rejeitar-troca/', rejeitar_troca_guarda, name='rejeitar_troca'),
    path('executar-troca/', executar_troca_guarda, name='executar_troca'),
    path('trocas_detalhadas/', trocas_detalhadas, name='trocas_detalhadas'),
    path('feriados/', listar_feriados, name='feriados'),
    path('notificacoes/marcar_todas_lidas/', marcar_todas_como_lidas, name='marcar_todas_lidas'),
    path('cadastrar_usuario/', cadastrar_usuario, name='cadastrar_usuario'),
    path('deletar_usuario/<int:id>/', deletar_usuario, name='deletar_usuario'),

]
urlpatterns = router.urls + custom_urls