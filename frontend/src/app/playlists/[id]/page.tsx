'use client';
import useIdFromParams from "@/src/hooks/useIdFromParams";
import { usePlaylistQuery } from "@/src/hooks/playlists/usePlaylistQuery";
import { useEffect, useRef, useState } from "react";
import {Button} from "@nextui-org/react";

function PlaylistPage() {
    const id = useIdFromParams();
    const audioRef = useRef<HTMLAudioElement>(null);
    const [currentTrack, setCurrentTrack] = useState<number>(0);
    const [pause, setPause] = useState<'pause' | 'play'>('pause')
    const { data, isLoading } = usePlaylistQuery(id);
    const [isPlaying, setIsPlaying] = useState<boolean>(false);

    // Чтобы хуки всегда вызывались одинаково, используем заглушку для треков
    const tracks = data?.files || [];

    const playNext = () => {
        if (tracks.length > 0) {
            setCurrentTrack((prevIndex) => (prevIndex + 1) % tracks.length);
        }
    };

    const playPrev = () => {
        if (tracks.length > 0) {
            setCurrentTrack((prevIndex) => (prevIndex - 1 + tracks.length) % tracks.length);
        }
    }

    const togglePlayPause = () => {
        if (audioRef.current) {
            if (isPlaying) {
                audioRef.current.pause();
            } else {
                audioRef.current.play();
            }
            setIsPlaying(!isPlaying); // Меняем состояние
        }
    };

    useEffect(() => {
        if (audioRef.current && tracks.length > 0) {
            audioRef.current.play();
        }
    }, [currentTrack, tracks]);

    // Можно показывать индикатор загрузки, пока данные загружаются
    if (isLoading) {
        return <div>Loading...</div>;
    }

    if (tracks.length === 0) {
        return <div>No tracks available</div>;
    }

    return (
        <div>
            <div className='flex flex-row items-center justify-center gap-2'>
                <Button onClick={playPrev}>Prev</Button>
                <audio
                    ref={audioRef}
                    src={tracks[currentTrack]?.url}
                    controls
                    onEnded={playNext}
                    autoPlay={false}
                />
                <Button onClick={togglePlayPause}>{isPlaying ? "Pause" : "Play"}</Button>
                <Button onClick={playNext}>Next</Button>
            </div>
            <p>Сейчас играет: {tracks[currentTrack]?.name}</p>
        </div>
    );
}

export default PlaylistPage;
