import { INomenclatureByIdResponse } from '@/interfaces/Nomenclatures.interface';
import '../nomenclature.scss'
import { Skeleton } from '@mui/material';

interface SettingsProps {
    settings: INomenclatureByIdResponse['settings'] | undefined;
}

const Settings = (props: SettingsProps) => {

    const { settings } = props;

    return (
        <div className="settings">
            <div className="settings__default-volume">
                Громкость:
                <div className="settings__default-volume-item">
                    {
                        settings ?
                            settings.mon.default_volume.join(", ") :
                            <Skeleton
                                animation="pulse"
                                variant="text"
                                width='auto'
                                sx={{ bgcolor: '#f99f9f' }}
                            />
                    }
                </div>
            </div>
            <div className="settings__default-worktime">
                Режим работы:
                <div className="settings__default-worktime-item">
                    {
                        settings ?
                            settings.mon.worktime :
                            <Skeleton
                                animation="pulse"
                                variant="text"
                                width='auto'
                                sx={{ bgcolor: '#f99f9f' }}
                            />
                    }
                </div>
            </div>
            <div className="settings__title">
                <details>
                    <summary>Настройки по дням недели</summary>
                    <div className="settings__accordion">
                        {
                            settings ?
                                Object.entries(settings).map(([day, config]) => (
                                    <details key={day} className="settings__accordion-item">
                                        <summary>{day.toUpperCase()}</summary>
                                        <div className="settings__accordion-content">
                                            <div className="settings__accordion-custom">
                                                Индивидуальная громкость:
                                                <div className="settings__accordion-custom-item">
                                                    {Object.keys(config.custom_volume).length > 0 ? JSON.stringify(config.custom_volume) : "Не указано"}
                                                </div>
                                            </div>
                                        </div>
                                    </details>
                                )) :
                                Array.from({ length: 7 }).map((_, index) => (
                                    <div key={index} className="settings__accordion-skeleton">
                                        <Skeleton
                                            animation="wave"
                                            variant="text"
                                            width={200}
                                            height={20}
                                            sx={{ bgcolor: '#f99f9f', marginBottom: '10px' }}
                                        />
                                    </div>
                                ))
                        }
                    </div>
                </details>
            </div>
        </div>
    )
}

export default Settings;
