export async function sendNotification(queue: Queue, payload: Record<string, unknown>) {
  await queue.send(payload);
}
