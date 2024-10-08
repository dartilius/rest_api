'use client';
import useIdFromParams from "@/src/hooks/useIdFromParams";
import {useDeleteUserQuery, usePlaylistQuery} from "@/src/hooks/playlists/usePlaylistQuery";
import React, { useEffect, useRef, useState } from "react";
import {Button, Skeleton, Image} from "@nextui-org/react";
import { getMediaType } from "@/src/types/types/getMediaType";
import EditingPlaylistModal from "@/src/app/playlists/[id]/components/EditingPlaylistModal";
import DeletingModal from "@/src/components/ui/DeletingModal";
import styles from './PlaylistDetails.module.scss'


function PlaylistPage() {
    const id = useIdFromParams();
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const [currentTrack, setCurrentTrack] = useState<number>(0);
    const { data, isLoading } = usePlaylistQuery(id);
    const [isAutoPlay, setIsAutoPlay] = useState<boolean>(false);
    const [isPlaying, setIsPlaying] = useState<boolean>(false);
    const [openCreatingModal, setOpenCreatingModal] = useState<boolean>(false);
    const [openDeletingModal, setOpenDeletingModal] = useState<boolean>(false);
    const deletePlaylist = useDeleteUserQuery()

    // Чтобы хуки всегда вызывались одинаково, используем заглушку для треков
    const tracks = data?.files || [];

    const playNext = () => {
        if (tracks.length > 0) {
            setCurrentTrack((prevIndex) => (prevIndex + 1) % tracks.length);
            setIsAutoPlay(true);
        }
    };

    const playPrev = () => {
        if (tracks.length > 0) {
            setCurrentTrack((prevIndex) => (prevIndex - 1 + tracks.length) % tracks.length);
            setIsAutoPlay(true);
        }
    };

    const togglePlayPause = () => {
        if (audioRef.current) {
            if (isPlaying) {
                audioRef.current.pause();
            } else {
                audioRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    const playTrack = (index: number) => {
        setCurrentTrack(index);
        setIsAutoPlay(true); // Автовоспроизведение при выборе трека
    };

    // Автоматический переход в полноэкранный режим и воспроизведение видео
    const playFullscreen = () => {
        if (videoRef.current) {
            videoRef.current.play().then(() => {
                if (videoRef.current?.requestFullscreen) {
                    videoRef.current.requestFullscreen();
                }
            });
            setIsPlaying(true);
        }
    };

    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.play().catch((err) => {
                console.error("Ошибка при воспроизведении:", err);
            });
            setIsPlaying(true);
        }
    }, [currentTrack]);

    useEffect(() => {
        // Воспроизводим только если трек переключился автоматически
        if (audioRef.current && isAutoPlay) {
            audioRef.current.play();
            setIsPlaying(true); // Обновляем состояние воспроизведения
            setIsAutoPlay(false); // Сбрасываем флаг автопроигрывания
        }
    }, [currentTrack, isAutoPlay]);

    const type = getMediaType(tracks[currentTrack]?.name)
    // useEffect(() => {
    //     if (type === 'image') {
    //         setTimeout(() => {
    //             playNext()
    //         }, 10000)
    //     }
    //
    // }, [type, currentTrack]);

    const handleDeletePlaylist = () => {
        deletePlaylist.mutate(Number(id))
    }

    const handleCloseDeletingModal = () => {
        setOpenDeletingModal(false);
    };

    return (
        <div className={styles.container}>
            <div className={styles.container_info}>
                <div className='flex flex-row items-center gap-2'>
                    <h2>Название плейлиста</h2>
                    <span>{data?.name}</span>
                </div>
                <div className='flex flex-row items-center gap-2'>
                    <h2>Описание</h2>
                    <span>{data?.description}</span>
                </div>
                <div className='flex flex-row gap-2'>
                    <Button onClick={() => setOpenCreatingModal(true)} style={{width: '100%'}}>Edit</Button>
                    <Button color="danger" onClick={() => setOpenDeletingModal(true)} style={{width: '100%'}}>Delete</Button>
                </div>
            </div>
            <div className={styles.container_playerBlock}>
                {isLoading ? (
                    <Skeleton className="w-3/5 rounded-lg">
                        <div className="h-3 w-3/5 rounded-lg bg-default-200"></div>
                    </Skeleton>
                ) : (
                    <div className={styles.container_playerBlock_player}>
                        <p>Сейчас играет: {tracks[currentTrack]?.name}</p>
                        <div className={styles.container_playerBlock_player_block}>

                            {getMediaType(tracks[currentTrack]?.name) === 'video' && (
                                <div className="flex flex-col items-center gap-3">
                                    <video
                                        ref={videoRef}
                                        src={tracks[currentTrack]?.url}
                                        controls={true}
                                        onEnded={playNext} // Переход на следующее видео при завершении
                                        style={{height: 'auto'}}
                                    />
                                    <Button onClick={playFullscreen}>Play Fullscreen</Button>
                                </div>
                            )}
                            {getMediaType(tracks[currentTrack]?.name) === 'audio' && (
                                <div className="flex flex-col items-center gap-2">
                                    <audio
                                        ref={audioRef}
                                        src={tracks[currentTrack]?.url}
                                        controls
                                        onEnded={playNext}
                                        autoPlay={false}
                                    />
                                </div>
                            )}
                            {getMediaType(tracks[currentTrack]?.name) === 'image' && (
                                <Image
                                    src={tracks[currentTrack]?.url}
                                    alt={tracks[currentTrack]?.name}
                                    style={{height: '240px', width: 'auto'}}
                                />
                            )}
                            <div className="flex flex-row items-center gap-2">
                                <Button onClick={playPrev}>Prev</Button>
                                <Button onClick={playNext}>Next</Button>
                            </div>
                        </div>
                    </div>
                )}
                <div className={styles.container_playerBlock_files}>
                    <h2>Файлы</h2>
                    {data?.files.map((file, index) => (
                        <span
                            key={file.id}
                            onClick={() => playTrack(index)}
                            style={{
                                color: index === currentTrack ? 'green' : 'gray',
                                fontWeight: index === currentTrack ? 'bold' : 'normal',
                                cursor: 'pointer',
                            }}
                        >
                            {file.name}
                        </span>
                    ))}
                </div>
            </div>
            <DeletingModal
                close={handleCloseDeletingModal}
                deleteProp={handleDeletePlaylist}
                open={openDeletingModal}
            />
            <EditingPlaylistModal
                open={openCreatingModal}
                close={() => setOpenCreatingModal(false)}
                id={data?.id}
                filesPlaylist={data?.files}
                namePlaylist={data?.name}
                desc={data?.description}/>
        </div>
    );
}

export default PlaylistPage;
