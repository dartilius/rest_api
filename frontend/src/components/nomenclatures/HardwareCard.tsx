import {INomenclatureResponse} from "@/types/nomeclaturesType";
import {Name} from "@/components/data-display/Name";
import {Description} from "@/components/data-display/Description";

interface IHardwareCard {
    hardwareInfo: INomenclatureResponse['hw_info']
    className?: string;
}

function HardwareCard({hardwareInfo, className}: IHardwareCard) {
    return (
        <div className={`${className}`}>
            <div className='flex gap-3 items-baseline text-center'>
                <Name name='Серийный номер: ' className='font-bold text-lg'/>
                <Description description={hardwareInfo.serial_number} className='text-base'/>
            </div>
        </div>
    );
}

export default HardwareCard;