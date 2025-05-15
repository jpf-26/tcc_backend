from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import *
from .serializers import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, time



class UsuarioCustomizadoView(ModelViewSet):
    queryset = UsuarioCustomizado.objects.all()
    serializer_class = UsuarioCustomizadoSerializer

class GuardaView(ModelViewSet):
    queryset = Guarda.objects.all()
    serializer_class = GuardaSerializer

class UsuarioGuardaView(ModelViewSet):
    queryset = UsuarioGuarda.objects.all()
    serializer_class = UsuarioGuardaSerializer

@api_view(['POST'])
def upload_foto(request):
    if request.method == 'POST':
        serializer = UsuarioCustomizadoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    

class TrocaView(ModelViewSet):
    queryset = Troca.objects.all()
    serializer_class = TrocaSerializer

class TrocaAtiradorView(ModelViewSet):
    queryset = TrocaAtirador.objects.all()
    serializer_class = TrocaAtiradorSerializer

class TrocaGuardaView(ModelViewSet):
    queryset = TrocaGuarda.objects.all()
    serializer_class = TrocaGuardaSerializer

class NotificacaoView(ModelViewSet):
    queryset = Notificacao.objects.all()
    serializer_class = NotificacaoSerializer

class EscalaView(ModelViewSet):
    queryset = Escala.objects.all()
    serializer_class = EscalaSerializer


from rest_framework.decorators import api_view
import holidays
from holidays import Brazil
from datetime import timedelta
from rest_framework import status

@api_view(['POST'])
def sortear_guardas(request):
    try:
        ordem = request.data.get('ordem', 'crescente')
        data_inicio_str = request.data.get('data_inicio')
        data_fim_str = request.data.get('data_fim')

        if not data_inicio_str or not data_fim_str:
            return Response({'error': 'Data de início e fim são obrigatórias.'}, status=status.HTTP_400_BAD_REQUEST)

        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()

        todos_usuarios = list(UsuarioCustomizado.objects.order_by('numero_atirador'))
        atiradores = [u for u in todos_usuarios if u.comandante == 'N']
        comandantes = [u for u in todos_usuarios if u.comandante == 'S']

        if ordem == 'decrescente':
            atiradores.reverse()
            comandantes.reverse()

        if not atiradores or not comandantes:
            return Response({'error': 'É necessário ter ao menos um atirador e um comandante.'}, status=status.HTTP_400_BAD_REQUEST)

        feriados = holidays.Brazil(years=range(data_inicio.year, data_fim.year + 1))

        escala = Escala.objects.create(nome_escala=f"Escala de {data_inicio} a {data_fim}")

        index_uteis = 0
        index_especial = 0
        index_comandante_uteis = 0
        index_comandante_especial = 0

        def pegar_atiradores(indice):
            grupo = []
            for _ in range(3):
                grupo.append(atiradores[indice % len(atiradores)])
                indice += 1
            return grupo, indice

        for i in range((data_fim - data_inicio).days + 1):
            dia = data_inicio + timedelta(days=i)
            is_feriado = dia in feriados
            is_fds = dia.weekday() >= 5  # 5 = sábado, 6 = domingo
            tipo_especial = is_feriado or is_fds

            guarda = Guarda.objects.create(data_guarda=dia, observacoes='', id_escala=escala)

            if tipo_especial:
                grupo, index_especial = pegar_atiradores(index_especial)
                comandante = comandantes[index_comandante_especial % len(comandantes)]
                index_comandante_especial += 1
            else:
                grupo, index_uteis = pegar_atiradores(index_uteis)
                comandante = comandantes[index_comandante_uteis % len(comandantes)]
                index_comandante_uteis += 1

            for atirador in grupo:
                UsuarioGuarda.objects.create(id_guarda=guarda, numero_atirador=atirador, comandante=False)

            UsuarioGuarda.objects.create(id_guarda=guarda, numero_atirador=comandante, comandante=True)

        return Response({'mensagem': 'Sorteio realizado com sucesso!'}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






@api_view(['DELETE'])
def apagar_guardas(request):
    try:
        UsuarioGuarda.objects.all().delete()
        Guarda.objects.all().delete()
        Escala.objects.all().delete()

        return Response({'mensagem': 'Todas as guardas foram apagadas com sucesso!'}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 

from datetime import datetime

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def solicitar_troca_guarda(request):
    try:
        substituto_nome = request.data.get('substituto')
        data_solicitante = request.data.get('data_solicitante')
        data_substituto = request.data.get('data_substituto')
        motivo = request.data.get('motivo')

        if not all([substituto_nome, data_solicitante, data_substituto, motivo]):
            return Response({'erro': 'Dados incompletos.'}, status=400)

        data_solicitante = datetime.strptime(data_solicitante, "%Y-%m-%d").date()
        data_substituto = datetime.strptime(data_substituto, "%Y-%m-%d").date()

        
        if data_substituto < data_solicitante:
            return Response({'erro': 'A data da guarda do substituto não pode ser anterior à sua.'}, status=400)

        inicio_solic = datetime.combine(data_solicitante, time.min)
        fim_solic = datetime.combine(data_solicitante, time.max)
        inicio_subs = datetime.combine(data_substituto, time.min)
        fim_subs = datetime.combine(data_substituto, time.max)

        solicitante = request.user
        substituto = UsuarioCustomizado.objects.get(nome_guerra__iexact=substituto_nome)

        if solicitante.comandante != substituto.comandante:
            return Response({'erro': 'Comandantes só podem trocar com comandantes e atiradores com atiradores.'}, status=400)

        guarda_solicitante = UsuarioGuarda.objects.filter(
            numero_atirador=solicitante,
            id_guarda__data_guarda__range=(inicio_solic, fim_solic)
        ).first()

        if not guarda_solicitante:
            return Response({'erro': 'Você não está escalado na data informada.'}, status=404)

        guarda_substituto = UsuarioGuarda.objects.filter(
            numero_atirador=substituto,
            id_guarda__data_guarda__range=(inicio_subs, fim_subs)
        ).first()

        if not guarda_substituto:
            return Response({'erro': 'O substituto não está escalado na data informada.'}, status=404)

        
        if UsuarioGuarda.objects.filter(
            numero_atirador=solicitante,
            id_guarda__data_guarda__range=(inicio_subs, fim_subs)
        ).exists():
            return Response({'erro': 'Você já está escalado para a data da guarda do substituto.'}, status=400)

        
        if UsuarioGuarda.objects.filter(
            numero_atirador=substituto,
            id_guarda__data_guarda__range=(inicio_solic, fim_solic)
        ).exists():
            return Response({'erro': 'O substituto já está escalado para a data da sua guarda.'}, status=400)

        troca = Troca.objects.create(motivo=motivo)

        TrocaAtirador.objects.create(id_troca=troca, numero_atirador=solicitante, tipo='Solicitante')
        TrocaAtirador.objects.create(id_troca=troca, numero_atirador=substituto, tipo='Substituto')

        TrocaGuarda.objects.create(id_troca=troca, id_guarda=guarda_solicitante.id_guarda)
        TrocaGuarda.objects.create(id_troca=troca, id_guarda=guarda_substituto.id_guarda)

        Notificacao.objects.create(
            numero_atirador=substituto,
            mensagem="Você possui uma solicitação de troca de guarda pendente... Olhe suas solicitações de troca! ",
            status="Pendente",
            id_troca=troca
        )

        return Response({'mensagem': 'Solicitação registrada com sucesso.', 'id_troca': troca.id}, status=201)

    except UsuarioCustomizado.DoesNotExist:
        return Response({'erro': 'Substituto não encontrado.'}, status=404)
    except Exception as e:
        print("ERRO:", str(e))
        return Response({'erro': str(e)}, status=500)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aceitar_troca(request):
    try:
        id_troca = request.data.get('id_troca')
        if not id_troca:
            return Response({'erro': 'ID da troca não fornecido.'}, status=400)

        troca = Troca.objects.get(id=id_troca)
        user = request.user

        substituto_rel = TrocaAtirador.objects.filter(id_troca=troca, tipo='Substituto', numero_atirador=user).first()
        if not substituto_rel:
            return Response({'erro': 'Você não é o substituto desta troca.'}, status=403)

        solicitante_rel = TrocaAtirador.objects.get(id_troca=troca, tipo='Solicitante')
        solicitante = solicitante_rel.numero_atirador
        substituto = substituto_rel.numero_atirador

        
        troca.status = 'Aceita'
        troca.save()

        
        Notificacao.objects.filter(id_troca=id_troca, numero_atirador=substituto.numero_atirador).update(status='Lida')

        
        Notificacao.objects.create(
            numero_atirador=solicitante,
            mensagem=f"{substituto.nome_guerra} aceitou a sua solicitação de troca de guarda.",
            status="Pendente",
            id_troca=troca
        )

        
        guardas = TrocaGuarda.objects.filter(id_troca=troca).select_related('id_guarda')
        data_solicitante = guardas[0].id_guarda.data_guarda.strftime('%d/%m/%Y') if len(guardas) > 0 else 'Data 1'
        data_substituto = guardas[1].id_guarda.data_guarda.strftime('%d/%m/%Y') if len(guardas) > 1 else 'Data 2'

        
        admins = UsuarioCustomizado.objects.filter(role='admin')
        for admin in admins:
            Notificacao.objects.create(
                numero_atirador=admin,
                mensagem=(
                    f"{solicitante.nome_guerra} trocou sua guarda do dia {data_solicitante} com "
                    f"{substituto.nome_guerra} guarda no dia {data_substituto}. "
                    f"A troca foi aceita em {datetime.now().strftime('%d/%m/%Y')}."
                ),
                status="Pendente",
                id_troca=troca
            )

        return Response({'mensagem': 'Troca aceita com sucesso!'}, status=200)

    except Troca.DoesNotExist:
        return Response({'erro': 'Troca não encontrada.'}, status=404)
    except Exception as e:
        return Response({'erro': str(e)}, status=500)



    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rejeitar_troca_guarda(request):
    try:
        id_troca = request.data.get('id_troca')

        if not id_troca:
            return Response({'erro': 'ID da troca não fornecido.'}, status=status.HTTP_400_BAD_REQUEST)

        troca = Troca.objects.get(id=id_troca)

        if troca.status.lower() != 'pendente':
            return Response({'erro': 'A troca já foi processada.'}, status=status.HTTP_400_BAD_REQUEST)

        
        substituto_atirador = TrocaAtirador.objects.get(id_troca=troca, tipo='Substituto')

       
        if request.user != substituto_atirador.numero_atirador:
            return Response({'erro': 'Você não tem permissão para recusar esta troca.'}, status=status.HTTP_403_FORBIDDEN)

        
        troca.status = 'Rejeitada'
        troca.save()

        
        Notificacao.objects.filter(id_troca=id_troca, numero_atirador=request.user.numero_atirador).update(status='Lida')

        
        solicitante = TrocaAtirador.objects.get(id_troca=troca, tipo='Solicitante').numero_atirador

        Notificacao.objects.create(
            numero_atirador=solicitante,
            mensagem=f"{substituto_atirador.numero_atirador.nome_guerra} recusou a sua solicitação de troca de guarda.",
            status="Pendente",
            id_troca=troca
        )

        return Response({'mensagem': 'Troca rejeitada com sucesso.'}, status=status.HTTP_200_OK)

    except Troca.DoesNotExist:
        return Response({'erro': 'Troca não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    except TrocaAtirador.DoesNotExist:
        return Response({'erro': 'Dados do substituto não encontrados.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'erro': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def executar_troca_guarda(request):
    try:
        id_troca = request.data.get('id_troca')

        if not id_troca:
            return Response({'erro': 'ID da troca não fornecido.'}, status=status.HTTP_400_BAD_REQUEST)

        troca = Troca.objects.get(id=id_troca)

        if troca.status.lower() != 'aceita':
            return Response({'erro': 'A troca não está aceita.'}, status=status.HTTP_400_BAD_REQUEST)

        
        solicitante_rel = TrocaAtirador.objects.get(id_troca=troca, tipo='Solicitante')
        substituto_rel = TrocaAtirador.objects.get(id_troca=troca, tipo='Substituto')
        solicitante = solicitante_rel.numero_atirador
        substituto = substituto_rel.numero_atirador

        
        guardas_troca = TrocaGuarda.objects.filter(id_troca=troca)

        
        guarda_solicitante = None
        guarda_substituto = None

        for g in guardas_troca:
            if UsuarioGuarda.objects.filter(numero_atirador=solicitante, id_guarda=g.id_guarda).exists():
                guarda_solicitante = g.id_guarda
            elif UsuarioGuarda.objects.filter(numero_atirador=substituto, id_guarda=g.id_guarda).exists():
                guarda_substituto = g.id_guarda

        if not guarda_solicitante or not guarda_substituto:
            return Response({'erro': 'Não foi possível identificar as guardas dos envolvidos.'}, status=status.HTTP_400_BAD_REQUEST)

       
        ug_solicitante = UsuarioGuarda.objects.get(numero_atirador=solicitante, id_guarda=guarda_solicitante)
        ug_substituto = UsuarioGuarda.objects.get(numero_atirador=substituto, id_guarda=guarda_substituto)

        ug_solicitante.numero_atirador, ug_substituto.numero_atirador = substituto, solicitante
        ug_solicitante.save()
        ug_substituto.save()

        
        troca.status = 'executada'
        troca.save()

        return Response({'mensagem': 'Troca realizada com sucesso.'}, status=status.HTTP_200_OK)

    except Troca.DoesNotExist:
        return Response({'erro': 'Troca não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    except TrocaAtirador.DoesNotExist:
        return Response({'erro': 'Dados da troca incompletos.'}, status=status.HTTP_400_BAD_REQUEST)
    except UsuarioGuarda.DoesNotExist:
        return Response({'erro': 'Vínculo entre atirador e guarda não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'erro': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def guardas_agrupadas(request):
    guardas = Guarda.objects.all().order_by('data_guarda')
    resultado = []

    for guarda in guardas:
        usuarios = UsuarioGuarda.objects.filter(id_guarda=guarda)
        atiradores = usuarios.filter(comandante=False).values_list('numero_atirador__nome_guerra', flat=True)
        comandante = usuarios.filter(comandante=True).first()

        data_ref = guarda.data_guarda.strftime('%d/%m/%Y')

        resultado.append({
            "id": guarda.id,
            "data-ref": data_ref,
            "id_guarda": guarda.id,
            "atirador_1": atiradores[0] if len(atiradores) > 0 else None,
            "atirador_2": atiradores[1] if len(atiradores) > 1 else None,
            "atirador_3": atiradores[2] if len(atiradores) > 2 else None,
            "comandante": comandante.numero_atirador.nome_guerra if comandante else None
        })

    return Response(resultado)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trocas_detalhadas(request):
    try:
        trocas = Troca.objects.filter(status='Pendente')
        resultado = []

        for troca in trocas:
            solicitante_obj = TrocaAtirador.objects.filter(id_troca=troca, tipo='Solicitante').first()
            substituto_obj = TrocaAtirador.objects.filter(id_troca=troca, tipo='Substituto').first()

            if not solicitante_obj or not substituto_obj:
                continue

            guarda_solic = UsuarioGuarda.objects.filter(
                numero_atirador=solicitante_obj.numero_atirador,
                id_guarda__trocaguarda__id_troca=troca
            ).first()

            guarda_subs = UsuarioGuarda.objects.filter(
                numero_atirador=substituto_obj.numero_atirador,
                id_guarda__trocaguarda__id_troca=troca
            ).first()

            resultado.append({
                'id_troca': troca.id,
                'motivo': troca.motivo,
                'solicitante': solicitante_obj.numero_atirador.nome_guerra,
                'substituto': substituto_obj.numero_atirador.nome_guerra,
                'id_solicitante': solicitante_obj.numero_atirador.id,
                'id_substituto': substituto_obj.numero_atirador.id,
                'data_guarda_solicitante': guarda_solic.id_guarda.data_guarda if guarda_solic else None,
                'data_guarda_substituto': guarda_subs.id_guarda.data_guarda if guarda_subs else None,
                'status': troca.status,
            })

        return Response(resultado)
    except Exception as e:
        return Response({'erro': str(e)}, status=500)


@api_view(['GET'])
def listar_feriados(request):
    try:
        ano = datetime.now().year
        feriados = Brazil(years=ano)
        feriados_json = [
            {'data': str(data), 'nome': nome}
            for data, nome in feriados.items()
        ]
        return Response(feriados_json, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'erro': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_todas_como_lidas(request):
    try:
        user = request.user
        Notificacao.objects.filter(numero_atirador=user, status='Pendente').update(status='Lida')
        return Response({'mensagem': 'Todas as notificações foram marcadas como lidas.'}, status=200)
    except Exception as e:
        return Response({'erro': str(e)}, status=500)

