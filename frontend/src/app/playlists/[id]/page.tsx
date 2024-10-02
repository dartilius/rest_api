'use client';
import useIdFromParams from "@/src/hooks/useIdFromParams";
import {usePlaylistQuery} from "@/src/hooks/playlists/usePlaylistQuery";
import styles from './PlaylistDetails.module.scss'

function PlaylistPage() {
    const id = useIdFromParams()
    const {data, isLoading} = usePlaylistQuery(id)

    if (!data) return null;

    return (
        <div className={styles.container}>
            <div className={styles.container_description}>
                <div className={styles.container_description_name}>
                    <label className={styles.label}>Название</label>
                    <span className={styles.span}>{data.name}</span>
                </div>
                <div className={styles.container_description_desc}>
                    <h2>Описание</h2>
                    <span>{data.description}</span>
                </div>
                <div className={styles.container_description_owner}>
                    <h3>Создатель</h3>
                    <span>{data.owner}</span>
                </div>
            </div>
        </div>
    );
}

export default PlaylistPage;