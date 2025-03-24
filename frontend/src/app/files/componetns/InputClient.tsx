"use client";
import {useState, useRef, FormEvent} from "react";

export default function InputClient() {
    const [inputValue, setInputValue] = useState("");
    const inputRef = useRef<HTMLInputElement | null>(null);

    const handleInput = (e: FormEvent<HTMLInputElement>) => {
        const value = e.currentTarget.value;
        setInputValue(value);

        if (inputRef.current) {
            if (value.trim()) {
                inputRef.current.setAttribute("name", "name");
            } else {
                inputRef.current.removeAttribute("name");
            }
        }

        e.currentTarget.form?.requestSubmit();
    };

    return (
        <input
            ref={inputRef}
            type="text"
            style={{ color: "black" }}
            placeholder="Введите запрос..."
            value={inputValue}
            onInput={handleInput}
        />
    );
}
