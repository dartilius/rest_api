import React, {useEffect, useState} from 'react';
import styles from './CustomTextArea.module.scss'; // Assuming you're using SCSS for styles

type Props = {
    placeholder: string;
    desc: string;
    // editable: boolean;
}

const CustomTextarea = (props: Props) => {
    const [text, setText] = useState('');
    // const [canEdit, setCanEdit] = useState(false);
    const maxChars = 500;
    const {placeholder, desc} = props

    useEffect(() => {
        setText(desc)
    }, [desc]);

    // useEffect(() => {
    //     setCanEdit(editable);
    // }, [editable]);

    return (
        <div className={styles.custom_textarea}>
            <label className={styles.label}>{placeholder}</label>
            <textarea
                placeholder={placeholder}
                value={text}
                onChange={(e) => setText(e.target.value)}
                maxLength={maxChars}
                className={styles.textarea}
                // disabled={!canEdit}
            />
            <div className={styles.footer}>
                <span className={styles.char_counter}>{`${text.length}/${maxChars}`}</span>
            </div>
        </div>
    );
};

export default CustomTextarea;
