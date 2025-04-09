'use client'

import { useState, useEffect } from "react";
import { getTagList } from "@/services/FilesService";
import { ITagResponse } from "@/types/fileTypes";

interface SelectTagsProps {
    onChange: (tags: ITagResponse[]) => void;
}

function SelectTags({ onChange }: SelectTagsProps) {
    const [tags, setTags] = useState<ITagResponse[]>([]);
    const [selectedTags, setSelectedTags] = useState<ITagResponse[]>([]);
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        const fetchTags = async () => {
            try {
                const res = await getTagList();
                console.log(res)
                setTags(res.results);
            } catch (e: any) {
                console.error(e);
            }
        };
        fetchTags();
    }, []);

    const toggleTag = (tag: ITagResponse) => {
        const alreadySelected = selectedTags.some(t => t.id === tag.id);
        const updated = alreadySelected
            ? selectedTags.filter(t => t.id !== tag.id)
            : [...selectedTags, tag];

        setSelectedTags(updated);
        onChange(updated);
    };

    const isSelected = (tag: ITagResponse) =>
        selectedTags.some(t => t.id === tag.id);

    console.log('tags', tags)

    return (
        <div style={{ position: 'relative' }}>
            <button onClick={() => setIsOpen(prev => !prev)}>
                Выбрать теги
            </button>

            {isOpen && (
                <ul style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    background: 'white',
                    border: '1px solid #ccc',
                    listStyle: 'none',
                    padding: 0,
                    margin: 0,
                    zIndex: 1000,
                    maxHeight: '200px',
                    overflowY: 'auto',
                    width: '200px',
                }}>
                    {tags?.map(tag => (
                        <li
                            key={tag.id}
                            onClick={() => toggleTag(tag)}
                            style={{
                                padding: '8px',
                                cursor: 'pointer',
                                backgroundColor: isSelected(tag) ? '#e0f7fa' : 'white'
                            }}
                        >
                            {tag.name}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default SelectTags;
