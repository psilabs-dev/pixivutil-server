# Metadata API

`POST /api/queue/metadata/artwork/{artwork_id}`

Queue download of artwork metadata by ID.

`POST /api/queue/metadata/member/{member_id}`

Queue download of member metadata by ID.

`POST /api/queue/metadata/series/{series_id}`

Queue download of series metadata by ID.

`POST /api/queue/metadata/tag/{tag}`

Queue download of tag metadata by tag name. Optional query: `filter_mode` in
`none`, `pixpedia`, `translation`, `pixpedia_or_translation`.
