'use client'
import React, {useState} from 'react';
import {Collapse} from "@mui/material";

function CollapsWrapper({children}: {children: React.ReactNode}) {
    const [open, setOpen] = useState(false);
    return (
        <div>
            <button onClick={() => setOpen(true)}>open</button>
            <Collapse in={open}>
                {children}
            </Collapse>
        </div>
    );
}

export default CollapsWrapper;