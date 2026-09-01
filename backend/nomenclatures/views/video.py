from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from drf_spectacular.utils import extend_schema

from api.constants import get_instance_or_404
from api.mixins import SignedMediaNoCacheMixin
from users.permissions import StaffCUDallRead
from ..models import Nomenclature, NomenclatureVideo
from ..serializers import VideoSerializer


@extend_schema(tags=["Видео номенклатур", "Номенклатуры"])
class NomenclatureVideoViewSet(SignedMediaNoCacheMixin, viewsets.ModelViewSet):
    """Загрузка, просмотр и удаление видеозаписей номенклатур."""

    queryset = NomenclatureVideo.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [StaffCUDallRead]
    http_method_names = ["get", "post", "delete", "patch"]

    @extend_schema(
        summary="Прикрепить видео к номенклатуре",
        request=VideoSerializer,
        responses={HTTP_201_CREATED: VideoSerializer},
    )
    @action(methods=["POST"], detail=True, url_path="add_video")
    def add_video(self, request, pk):
        nomenclature = get_instance_or_404(Nomenclature, pk=pk)
        serializer = VideoSerializer(
            data=request.data,
            context={"nomenclature": nomenclature},
        )
        serializer.is_valid(raise_exception=True)
        video = serializer.save()
        return Response(VideoSerializer(video).data, status=HTTP_201_CREATED)

    @action(methods=["GET"], detail=False)
    def get_videos(self, request):
        videos = NomenclatureVideo.objects.filter(nomenclature__isnull=False)
        return Response(VideoSerializer(videos, many=True).data, status=HTTP_200_OK)

    @action(methods=["GET"], detail=True)
    def get_nomenclature_videos(self, request, pk):
        nomenclature = get_instance_or_404(Nomenclature, pk)
        return Response(
            VideoSerializer(nomenclature.videos.all(), many=True).data,
            status=HTTP_200_OK,
        )
