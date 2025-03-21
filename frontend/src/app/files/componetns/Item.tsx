import {Button, Card, CardActions, CardContent} from "@mui/material";
import {FilesDataList} from "@/services/FilesService";
import {convertSizeFile, convertTypeFile} from "@/utils";
import Page from "@/app/files/[id]/page";

type Props = {
    item: FilesDataList
}

export function Item(props: Props) {

    const {item} = props
    const {name, id, type, length, size} = item
        
    return (
        <Card sx={{
            maxWidth: 360,
            color: 'black',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            height: 272 // Фиксированная высота карточки
        }}>
            <CardContent>
                <div>
                    {convertTypeFile(type.toString())}
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