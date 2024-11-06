import styles from './Input.module.scss'
import {InputHTMLAttributes} from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
    label: string;
};

export function Input({ label, ...inputProps }: InputProps) {

    return (
        <div className={styles.input_box}>
            <label className={styles.input_box__label}>{label}</label>
            <input className={styles.input_box__input} type='text' {...inputProps} />
        </div>
    );
}