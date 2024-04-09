# Configuration

For more fine-tuned configuration, use `.pixivUtil2/conf/conf.ini` (refer to [Pixivutil2](https://github.com/Nandaka/PixivUtil2)).

## Default Configurations
`PixivUtil2` configuration defaults are modified:

- `downloadListDirectory="./downloads"`
- `rootDirectory="."`
- `dbPath=".pixivUtil2/db/db.sqlite"`
- `useragent="Mozilla/5.0"`
- `filenameFormat='{%member_id%} %artist%/{%image_id%} %title%/%page_number%'`
- `filenameMangaFormat='{%member_id%} %artist%/{%image_id%} %title%/%page_number%'`

## Environment Variable Configuration

Supported environment variable overrides. See `PixivServer/configuration/pixivutil.py`.