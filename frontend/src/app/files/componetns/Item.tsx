import {Button, Card, CardActions, CardContent} from "@mui/material";
import {FilesDataList} from "@/services/FilesService";
import {convertSizeFile} from "@/utils";
import Page from "@/app/files/[id]/page";
import AudiotrackTwoToneIcon from '@mui/icons-material/AudiotrackTwoTone';
import ImageTwoToneIcon from '@mui/icons-material/ImageTwoTone';
import VideoFileTwoToneIcon from '@mui/icons-material/VideoFileTwoTone';

type Props = {
    item: FilesDataList
}

export function Item(props: Props) {

    const {item} = props
    const {name, id, type, length, size} = item
    console.log(type)
    return (
        <Card sx={{
            maxWidth: 360,
            color: 'black',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            maxHeight: 390,
            height: '100%',
            width: '100%',
        }}>
            <CardContent>
                <div>
                    {type === 'music' && (
                        <div style={{display: 'flex', flexDirection: 'row', gap: '12px'}}>
                            <AudiotrackTwoToneIcon />
                            {name}
                        </div>

                    )}
                    {type === 'image' && (
                        <div style={{display: 'flex', flexDirection: 'row', gap: '12px'}}>
                            <ImageTwoToneIcon />
                            {name}
                        </div>
                    )}
                    {type === 'video' && (
                        <div style={{display: 'flex', flexDirection: 'row', gap: '12px'}}>
                            <VideoFileTwoToneIcon />
                            {name}
                        </div>
                    )}
                </div>
            </CardContent>
            <CardContent>
                    <Page params={{id}}/>
            </CardContent>
            <CardContent>
                <div>
                    {length && (length)}
                </div>
                <div>
                    {size && (convertSizeFile(size))}
                </div>
            </CardContent>
            <CardActions>
                <Button size="small">Share</Button>
                <Button size="small">Learn More</Button>
            </CardActions>

        </Card>
    );
}