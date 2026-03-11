# Dead Letter Queue API

Authentication:
- Requires `Authorization: Bearer <api-key>` when `PIXIVUTIL_SERVER_API_KEY` is set.
- If `PIXIVUTIL_SERVER_API_KEY` is unset/empty, authentication is disabled.

Dead letter queue (DLQ) endpoints manage failed worker messages that were moved
to the broker dead letter queue after retry exhaustion or terminal failure.

`GET /api/queue/dead-letter/`

List all messages currently in the dead letter queue.

Response item shape:
- `dead_letter_id`: message/task identifier (string)
- `task_name`: registered Celery task name (string)
- `payload`: original task payload (object)

`POST /api/queue/dead-letter/resume`

Requeue all resumable dead letter messages back to the main worker queue.

Response:
- `requeued`: number of messages requeued

Notes:
- Messages with unknown/unregistered task names are left in the DLQ.
- Unparseable messages are left in the DLQ.

`POST /api/queue/dead-letter/{dead_letter_id}/resume`

Requeue a specific dead letter message by `dead_letter_id`.

Response:
- `dead_letter_id`: requested DLQ message id
- `requeued`: `true` when message was requeued
- `task_name`: task name that was requeued

Errors:
- `404`: dead letter message not found
- `422`: task name is not recognized and cannot be resumed

`DELETE /api/queue/dead-letter/`

Purge all messages from the dead letter queue.

Response:
- `dropped`: number of messages removed

`DELETE /api/queue/dead-letter/{dead_letter_id}`

Drop a specific dead letter message by `dead_letter_id`.

Response:
- `dead_letter_id`: requested DLQ message id
- `dropped`: `true` when message was removed

Errors:
- `404`: dead letter message not found
