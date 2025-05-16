from rest_framework import serializers
from .models import *

class UsuarioCustomizadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioCustomizado
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'foto': {'required': False},
        }

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "POST":
            self.fields['password'].required = True
            self.fields['foto'].required = True  # Apenas no POST
        else:
            self.fields['password'].required = False
            self.fields['foto'].required = False

    def create(self, validated_data):
        # Remove campos ManyToMany que causam erro
        validated_data.pop("groups", None)
        validated_data.pop("user_permissions", None)

        senha = validated_data.pop("password")
        instance = UsuarioCustomizado.objects.create_user(**validated_data)
        instance.set_password(senha)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        senha = validated_data.pop("password", None)
        validated_data.pop("groups", None)
        validated_data.pop("user_permissions", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if senha:
            instance.set_password(senha)
        instance.save()
        return instance



class GuardaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guarda
        fields = '__all__'

class UsuarioGuardaSerializer(serializers.ModelSerializer):
    nome_guerra = serializers.CharField(source='numero_atirador.nome_guerra', read_only=True)

    class Meta:
        model = UsuarioGuarda
        fields = ['id', 'id_guarda', 'comandante', 'nome_guerra']

class TrocaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Troca
        fields = '__all__'

class TrocaAtiradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrocaAtirador
        fields = '__all__'

class TrocaGuardaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrocaGuarda
        fields = '__all__'

class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = '__all__'

class EscalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Escala
        fields = '__all__'    
        
