from .models import Sample
from rest_framework import status
from rest_framework import viewsets
from .serializer import SampleSerializer
from rest_framework.response import Response

# Create your views here.

class SampleView(viewsets.ModelViewSet): 
    serializer_class = SampleSerializer
    queryset = Sample.objects.all()
    
    
    def create(self, request, *args, **kwargs):
        
        data = request.data

        print(data)

        # Supongamos que determinamos el barrio y lo almacenamos en la variable neighbourhood
        neighbourhood = "Barrio determinado"

        # Agregar el barrio al diccionario de datos
        data['neighbourhood'] = neighbourhood

        # Crear una instancia del serializador con los datos procesados
        serializer = self.get_serializer(data=data)

        # Validar los datos
        if serializer.is_valid():
            # Guardar la instancia
            serializer.save()
            # Devolver una respuesta de éxito con los datos de la instancia creada y el estado HTTP 201 Created
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        # Si los datos no son válidos, devolver una respuesta de error con los detalles de la validación y el estado HTTP 400 Bad Request
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)