'use client';
import useIdFromParams from "@/src/hooks/useIdFromParams";
import { usePlaylistQuery } from "@/src/hooks/playlists/usePlaylistQuery";
import { useEffect, useRef, useState } from "react";
import { Button, Skeleton } from "@nextui-org/react";

function PlaylistPage() {
    const id = useIdFromParams();
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const [currentTrack, setCurrentTrack] = useState<number>(0);
    const { data, isLoading } = usePlaylistQuery(id);
    const [isAutoPlay, setIsAutoPlay] = useState<boolean>(false);
    const [isPlaying, setIsPlaying] = useState<boolean>(false);

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

    useEffect(() => {
        // Воспроизводим только если трек переключился автоматически
        if (audioRef.current && isAutoPlay) {
            audioRef.current.play();
            setIsPlaying(true); // Обновляем состояние воспроизведения
            setIsAutoPlay(false); // Сбрасываем флаг автопроигрывания
        }
    }, [currentTrack, isAutoPlay]);

    return (
        <>
            <div>
                {isLoading ? (
                    <Skeleton className="w-3/5 rounded-lg">
                        <div className="h-3 w-3/5 rounded-lg bg-default-200"></div>
                    </Skeleton>
                ) : (
                    <div className='flex flex-col justify-center items-center gap-3'>
                        <p>Сейчас играет: {tracks[currentTrack]?.name}</p>
                        <div className='flex flex-row items-center justify-center gap-2'>
                            <Button onClick={playPrev}>Prev</Button>
                            <audio
                                ref={audioRef}
                                src={tracks[currentTrack]?.url}
                                controls={false}
                                onEnded={playNext}
                                autoPlay={false}
                            />
                            <Button onClick={togglePlayPause}>
                                {isPlaying ? "Pause" : "Play"}
                            </Button>
                            <Button onClick={playNext}>Next</Button>
                        </div>
                    </div>
                )}
            </div>
            <div>
                <div className='flex flex-row items-center gap-2'>
                    <h2>Название плейлиста</h2>
                    <span>{data?.name}</span>
                </div>
                <div className='flex flex-row items-center gap-2'>
                    <h2>Описание</h2>
                    <span>{data?.description}</span>
                </div>
                <div className='flex flex-col'>
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
        </>
    );
}

export default PlaylistPage;
