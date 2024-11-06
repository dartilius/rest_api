import React, {ButtonHTMLAttributes} from 'react';
import Arrow from '@/src/styles/icons/arrow-back.svg'
import style from '../Button.module.scss'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement>

export function ButtonBack({...buttonProps}: ButtonProps) {
    return (
        <div className={style.button}>
            <Arrow height={24} width={24} {...buttonProps} />
        </div>
    );
}