# Запросы

- ### Номенклатура

#### Общий список

```
url = 'http://.../nomenclature/'
queryParams = {
    page: number,
    limit: number,
    name: string,
    status: string,
    timezone: string,
    version: string,
}
метод: getNomenclatureList(queryParams)
путь до метода: project/frontend/src/services/NomenclatureService.ts
```

#### Расшифровка номенклатуры по id
```
url = 'http://.../nomenclature/{id}'
метод: getNomenclatureDetail(id)
путь до метода: project/frontend/src/services/NomenclatureService.ts
```

#### Экшены номенклатуры в расшифровке
```
    - Переотправка заказа
        url = 'http://.../nomenclatures/${id}/resend_orders/'
        метод: resendOrders(id)
        путь до метода: project/frontend/src/services/NomenclatureService.ts
        
    - отправить экшены
        url = 'http://.../nomenclatures/${id}/actions/'
        метод: sendActions(id, type, parameters('not required') )
        путь до метода: project/frontend/src/services/NomenclatureService.ts
        что включает: 
            type - 'update', 'reboot', 'command' (string)
            parameters - это сама команда bash, если выбран type 'command' (string)
```

#### Удаление номенклатуры
```
url = 'http://.../nomenclature/{id}'
метод: deleteNomenclatures(id)
путь до метода: project/frontend/src/services/NomenclatureService.ts
```

#### Создание номенклатуры
```
url = 'http://.../nomenclature/{id}/'
метод: createNomenclature(body)
путь до метода: project/frontend/src/services/NomenclatureService.ts
```

- ### Файлы

#### Список файлов
```
url = 'http://.../files'
queryParams = {
    page: number,
    limit: number,
    name: string,
    file_type: string,
    tags: string[],
}
метод: getFilesList(queryParams)
- теги в query добавляются через &tags=tags1&tags=tags2...
путь до метода: project/frontend/src/services/FilesService.ts
```

#### Расшифровка файла по id
```
url = 'http://.../files/{id}'
метод: getFileDetail(id)
путь до метода: project/frontend/src/services/FilesService.ts
```

#### Добавить файл
```
url = 'http://.../files/'
метод: sendFile(body)
body = {
    type: number
    source: string
    tags: ITagResponse[]
}
путь до метода: project/frontend/src/services/FilesService.ts
```

#### Удалить фалй
```
url = 'http://.../files/{id}'
метод: deleteFile(id)
путь до метода: project/frontend/src/services/FilesService.ts
```

#### Редактировать файл (добавить тег(-и), открепить тег(-и))
```
url = 'http://.../files/${id}/add_tags/'
метод: addTags(id, tags)
    id: string
    tags: string[] (массив имен тегов)
путь до метода: project/frontend/src/services/FilesService.ts
```
```
url = 'http://.../files/${id}/remove_tags/'
метод: removeTags(id, tags)
    id: string
    tags: string[] (массив имен тегов)
путь до метода: project/frontend/src/services/FilesService.ts
```

#### Список тегов
```
url = 'http://.../tags'
queryParams = {
    page: number
}
метод: getTagList(queryParams)
путь до метода: project/frontend/src/services/FilesService.ts
```

#### Создать тег
```
url = 'http://.../tags/'
метод: createTag(name)
name: string
путь до метода: project/frontend/src/services/FilesService.ts
```

- ### Рекламные заказы

#### Список заказов
```
url = 'http://.../adorders'
queryParams = {
    page: number;
    limit: number;
    name: string;
    client: string;
    status: string;
    created_after: string;
    created_before: string;
    brc_type: string;
    since_after: string;
    since_before: string;
    until_after: string;
    until_before: string;
}
метод: getDataAd(queryParams)
путь до метода: project/frontend/src/app/adorders/api/index.ts
```

#### Расшифровка заказа по id
```
url = 'http://.../adorders/{id}'
метод: getAdOrderDetail(id)
путь до метода: project/frontend/src/app/adorders/api/index.ts
```

#### Отменить заказ
```
url = 'http://.../adorders/{id}/cancel/'
метод: cancelAdOrder(id)
путь до метода: project/frontend/src/app/adorders/api/index.ts
```

- ### Фоновые заказы

#### Список заказов
```
url = 'http://.../bgorders'
queryParams = {
    page: number;
    limit: number;
    name: string;
    client: string;
    status: string;
    created_after: string;
    created_before: string;
    order_type: string;
    since_after: string,
    since_before: string,
    until_after: string,
    until_before: string
}
метод: getDataBg(queryParams)
путь до метода: project/frontend/src/app/bgorders/api/index.ts
```

#### Расшифровка заказа по id
```
url = 'http://.../bgorders/{id}'
метод: getBgOrderDetail(id)
путь до метода: project/frontend/src/app/bgorders/api/index.ts
```

#### Отменить заказ
```
url = 'http://.../bgorders/{id}/cancel/'
метод: cancelBgOrder(id)
путь до метода: project/frontend/src/app/bgorders/api/index.ts
```

- ### Плейлисты

#### Список плейлистов
```
url = 'http://.../playlists'
queryParams = {
    id: string
    page: number;
    limit: number;
    name: string;
}
метод: getPlayLists(queryParams)
путь до метода: project/frontend/src/app/playlists/api/index.ts
```

#### Расшифровка плейлиста по id
```
url = 'http://.../playlists/{id}'
метод: getPlayListDetail(id)
путь до метода: project/frontend/src/app/playlists/api/index.ts
```


### Получить токен из куки
```
метод: getToken()
путь до метода: project/frontend/src/app/utils/getToken.ts
В зависимости от типа ренедера вызывается либо getClientAccessToken(), либо getServerAccessToken()
```