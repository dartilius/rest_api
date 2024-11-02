import React, {ButtonHTMLAttributes} from 'react';
import Arrow from '@/src/styles/icons/arrow-forward.svg'
import style from '../Button.module.scss'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement>

export function ButtonForward({...buttonProps}: ButtonProps) {
    return (
        <div className={style.button}>
            <Arrow height={24} width={24} {...buttonProps} />
        </div>
    );
}